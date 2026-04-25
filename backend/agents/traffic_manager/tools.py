from langchain_core.tools import tool
from typing import Optional
import structlog
import requests
from core.meta_client import (
    get_all_ad_accounts,
    create_campaign as meta_create_campaign,
    get_campaigns as meta_get_campaigns,
)
from core.meta_ads_builder import create_ad_set, build_targeting
from core.account_settings import get_account_settings_sync, save_account_settings_sync
from core.meta_insights import (
    get_campaigns_with_insights,
    get_campaign_insights_detail,
    activate_campaign,
    pause_campaign_api,
    update_campaign_budget,
    get_account_insights,
)
from core.config import settings

logger = structlog.get_logger()

OBJECTIVE_MAP = {
    "leads": "OUTCOME_LEADS",
    "trafego": "OUTCOME_TRAFFIC",
    "tráfego": "OUTCOME_TRAFFIC",
    "vendas": "OUTCOME_SALES",
    "conversoes": "OUTCOME_SALES",
    "conversões": "OUTCOME_SALES",
    "awareness": "OUTCOME_AWARENESS",
    "reconhecimento": "OUTCOME_AWARENESS",
    "engajamento": "OUTCOME_ENGAGEMENT",
}


@tool
def get_account_info(ad_account_id: str) -> dict:
    """Get saved settings for an ad account: WhatsApp number, website URL, Facebook Page ID.
    Always call this after the user selects an account to auto-fill known information."""
    try:
        cfg = get_account_settings_sync(ad_account_id)
        if not cfg:
            return {
                "success": True,
                "found": False,
                "message": "Nenhuma configuração salva para esta conta ainda.",
                "ad_account_id": ad_account_id,
            }
        whatsapp = cfg.get("whatsapp_number")
        wa_url = f"https://wa.me/{whatsapp}" if whatsapp else None
        return {
            "success": True,
            "found": True,
            "ad_account_id": ad_account_id,
            "account_name": cfg.get("account_name"),
            "whatsapp_number": whatsapp,
            "whatsapp_url": wa_url,
            "website_url": cfg.get("website_url"),
            "facebook_page_id": cfg.get("facebook_page_id"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def save_account_info(
    ad_account_id: str,
    account_name: str,
    whatsapp_number: str = "",
    website_url: str = "",
    facebook_page_id: str = "",
) -> dict:
    """Save account settings (WhatsApp, website, page ID) so they're auto-filled next time.
    whatsapp_number format: 5517991234567 (country code + area code + number, no spaces or symbols)"""
    try:
        result = save_account_settings_sync(
            ad_account_id=ad_account_id,
            account_name=account_name,
            whatsapp_number=whatsapp_number or None,
            website_url=website_url or None,
            facebook_page_id=facebook_page_id or None,
        )
        return {"success": True, "saved": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def list_ad_accounts() -> dict:
    """List all active Meta Ads accounts available to manage."""
    try:
        accounts = get_all_ad_accounts()
        active = [a for a in accounts if a["status"] == "Ativo"]
        return {"success": True, "active_count": len(active), "accounts": active}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def list_facebook_pages() -> dict:
    """List all Facebook Pages from all Business Managers. Required for ad creatives."""
    try:
        token = settings.META_ACCESS_TOKEN
        r = requests.get(
            "https://graph.facebook.com/v21.0/me/businesses",
            params={"fields": "id,name,owned_pages{id,name}", "access_token": token},
        )
        data = r.json()
        all_pages = []
        for bm in data.get("data", []):
            for page in bm.get("owned_pages", {}).get("data", []):
                all_pages.append({"id": page["id"], "name": page["name"], "business": bm.get("name", "")})
        return {"success": True, "pages": all_pages, "total": len(all_pages)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def validate_and_create_full_ad(
    ad_account_id: str,
    campaign_name: str,
    objective: str,
    daily_budget_brl: float,
    age_min: int,
    age_max: int,
    genders: list[int],
    countries: list[str],
    page_id: str,
    primary_text: str,
    headline: str,
    cta_button: str,
    link_url: str,
    image_url: str = "",
    activate_immediately: bool = True,
) -> dict:
    """Validate all parameters and create the complete ad structure (Campaign + Ad Set + Creative + Ad).
    Runs a pre-launch checklist before creating. Activates immediately if all checks pass.

    genders: [] = all, [1] = male, [2] = female
    cta_button: LEARN_MORE | SIGN_UP | SHOP_NOW | CONTACT_US | GET_QUOTE
    activate_immediately: True to go ACTIVE, False to stay PAUSED"""

    token = settings.META_ACCESS_TOKEN
    meta_objective = OBJECTIVE_MAP.get(objective.lower(), "OUTCOME_LEADS")

    # === PRE-LAUNCH CHECKLIST ===
    issues = []
    warnings = []

    if daily_budget_brl < 5:
        issues.append("Orçamento mínimo é R$5/dia para o Meta Ads.")
    if daily_budget_brl < 20:
        warnings.append(f"Orçamento de R${daily_budget_brl}/dia é baixo — pode limitar alcance. Recomendado: R$30+/dia.")
    if len(primary_text) > 500:
        issues.append("Texto principal muito longo (máx 500 chars).")
    if len(headline) > 40:
        issues.append(f"Headline muito longa: {len(headline)} chars (máx 40).")
    if not link_url.startswith("http"):
        issues.append("URL de destino inválida — deve começar com http:// ou https://.")
    if age_max - age_min < 5:
        warnings.append("Faixa etária muito estreita — pode limitar alcance.")
    if not image_url:
        warnings.append("Sem imagem — anúncio será criado apenas com texto.")

    if issues:
        return {"success": False, "validation_failed": True, "issues": issues, "warnings": warnings}

    status = "ACTIVE" if activate_immediately else "PAUSED"
    logger.info("creating_full_ad", account=ad_account_id, name=campaign_name, status=status)

    try:
        # 1. Campaign
        camp_r = requests.post(
            f"https://graph.facebook.com/v21.0/{ad_account_id}/campaigns",
            params={"access_token": token},
            json={
                "name": campaign_name,
                "objective": meta_objective,
                "status": status,
                "special_ad_categories": [],
                "is_adset_budget_sharing_enabled": False,
            },
        )
        camp = camp_r.json()
        if "error" in camp:
            return {"success": False, "step": "campaign", "error": camp["error"]["message"]}
        campaign_id = camp["id"]

        # 2. Ad Set
        targeting = build_targeting(
            age_min=age_min, age_max=age_max,
            genders=genders if genders else None,
            geo_locations={"countries": countries},
        )
        adset_r = requests.post(
            f"https://graph.facebook.com/v21.0/{ad_account_id}/adsets",
            params={"access_token": token},
            json={
                "name": f"{campaign_name} — Conjunto 01",
                "campaign_id": campaign_id,
                "daily_budget": int(daily_budget_brl * 100),
                "billing_event": "IMPRESSIONS",
                "optimization_goal": _get_optimization_goal(meta_objective),
                "targeting": targeting,
                "status": status,
            },
        )
        adset = adset_r.json()
        if "error" in adset:
            return {"success": False, "step": "ad_set", "error": adset["error"]["message"]}
        adset_id = adset["id"]

        # 3. Creative
        link_data: dict = {
            "link": link_url,
            "message": primary_text,
            "name": headline,
            "call_to_action": {"type": cta_button, "value": {"link": link_url}},
        }
        if image_url:
            link_data["picture"] = image_url

        creative_r = requests.post(
            f"https://graph.facebook.com/v21.0/{ad_account_id}/adcreatives",
            params={"access_token": token},
            json={
                "name": f"{campaign_name} — Criativo 01",
                "object_story_spec": {"page_id": page_id, "link_data": link_data},
            },
        )
        creative = creative_r.json()
        if "error" in creative:
            return {"success": False, "step": "creative", "error": creative["error"]["message"]}
        creative_id = creative["id"]

        # 4. Ad
        ad_r = requests.post(
            f"https://graph.facebook.com/v21.0/{ad_account_id}/ads",
            params={"access_token": token},
            json={
                "name": f"{campaign_name} — Anúncio 01",
                "adset_id": adset_id,
                "creative": {"creative_id": creative_id},
                "status": status,
            },
        )
        ad = ad_r.json()
        if "error" in ad:
            return {"success": False, "step": "ad", "error": ad["error"]["message"]}

        return {
            "success": True,
            "status": status,
            "campaign_id": campaign_id,
            "adset_id": adset_id,
            "creative_id": creative_id,
            "ad_id": ad["id"],
            "warnings": warnings,
            "message": f"Anúncio {'ATIVO' if activate_immediately else 'PAUSADO'} com sucesso!",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_account_performance(ad_account_id: str, days: int = 30) -> dict:
    """Get overall account performance metrics for the last N days.
    Returns spend, impressions, clicks, CTR, CPC, leads."""
    try:
        campaigns = get_campaigns_with_insights(ad_account_id, days)
        active = [c for c in campaigns if c["status"] == "ACTIVE"]
        total_spend = sum(c["insights"]["spend_brl"] for c in campaigns)
        total_leads = sum(c["insights"]["leads"] for c in campaigns)
        total_clicks = sum(c["insights"]["clicks"] for c in campaigns)
        total_impressions = sum(c["insights"]["impressions"] for c in campaigns)
        avg_ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions else 0
        avg_cpl = round(total_spend / total_leads, 2) if total_leads else None

        return {
            "success": True,
            "period_days": days,
            "summary": {
                "active_campaigns": len(active),
                "total_campaigns": len(campaigns),
                "total_spend_brl": round(total_spend, 2),
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_leads": total_leads,
                "avg_ctr_pct": avg_ctr,
                "avg_cpl_brl": avg_cpl,
            },
            "campaigns": campaigns,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def analyze_campaign_performance(campaign_id: str, days: int = 7) -> dict:
    """Analyze a specific campaign performance. Returns metrics, diagnosis and optimization recommendations."""
    try:
        data = get_campaign_insights_detail(campaign_id, days)
        rows = data.get("data", [])
        if not rows:
            return {"success": True, "campaign_id": campaign_id, "message": "Sem dados no período. A campanha pode estar muito nova ou sem veiculação."}

        total_spend = sum(float(r.get("spend", 0)) for r in rows)
        total_impressions = sum(int(r.get("impressions", 0)) for r in rows)
        total_clicks = sum(int(r.get("clicks", 0)) for r in rows)
        total_leads = sum(
            int(a.get("value", 0))
            for r in rows
            for a in r.get("actions", [])
            if a.get("action_type") in ("lead", "onsite_conversion.lead_grouped")
        )
        avg_ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions else 0
        avg_cpc = round(total_spend / total_clicks, 2) if total_clicks else 0
        cpl = round(total_spend / total_leads, 2) if total_leads else None

        # Diagnosis
        diagnosis = []
        recommendations = []

        if avg_ctr < 0.5:
            diagnosis.append("⚠️ CTR muito baixo (< 0.5%) — criativo não está chamando atenção.")
            recommendations.append("Teste um novo criativo com imagem mais impactante ou hook diferente.")
        elif avg_ctr >= 2.0:
            diagnosis.append("✅ CTR excelente (≥ 2%) — criativo performando bem.")

        if avg_cpc > 5:
            diagnosis.append(f"⚠️ CPC alto (R${avg_cpc}) — custo por clique acima do ideal.")
            recommendations.append("Refine o público ou aumente o orçamento para ganhar escala.")
        elif avg_cpc > 0 and avg_cpc <= 2:
            diagnosis.append(f"✅ CPC eficiente (R${avg_cpc}).")

        if total_impressions < 1000 and days >= 3:
            diagnosis.append("⚠️ Alcance muito baixo — público pode ser restrito ou orçamento insuficiente.")
            recommendations.append("Amplie a faixa etária ou aumente o orçamento diário.")

        if cpl and cpl > 50:
            diagnosis.append(f"⚠️ Custo por Lead alto (R${cpl}).")
            recommendations.append("Revise o formulário de leads ou a oferta do anúncio.")
        elif cpl and cpl <= 20:
            diagnosis.append(f"✅ Custo por Lead excelente (R${cpl}).")

        if not diagnosis:
            diagnosis.append("📊 Campanha em fase de aprendizado — aguarde mais dados.")

        return {
            "success": True,
            "campaign_id": campaign_id,
            "period_days": days,
            "metrics": {
                "spend_brl": round(total_spend, 2),
                "impressions": total_impressions,
                "clicks": total_clicks,
                "ctr_pct": avg_ctr,
                "cpc_brl": avg_cpc,
                "leads": total_leads,
                "cpl_brl": cpl,
            },
            "diagnosis": diagnosis,
            "recommendations": recommendations,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def activate_meta_campaign(campaign_id: str) -> dict:
    """Activate (turn on) a paused Meta Ads campaign."""
    try:
        result = activate_campaign(campaign_id)
        if "error" in result:
            return {"success": False, "error": result["error"]["message"]}
        return {"success": True, "campaign_id": campaign_id, "status": "ACTIVE"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def pause_meta_campaign(campaign_id: str) -> dict:
    """Pause an active Meta Ads campaign."""
    try:
        result = pause_campaign_api(campaign_id)
        if "error" in result:
            return {"success": False, "error": result["error"]["message"]}
        return {"success": True, "campaign_id": campaign_id, "status": "PAUSED"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def adjust_campaign_budget(campaign_id: str, new_daily_budget_brl: float, reason: str) -> dict:
    """Adjust the daily budget of a campaign based on performance analysis."""
    try:
        result = update_campaign_budget(campaign_id, new_daily_budget_brl)
        if "error" in result:
            return {"success": False, "error": result["error"]["message"]}
        return {
            "success": True,
            "campaign_id": campaign_id,
            "new_daily_budget_brl": new_daily_budget_brl,
            "reason": reason,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_optimization_goal(objective: str) -> str:
    return {
        "OUTCOME_LEADS": "LEAD_GENERATION",
        "OUTCOME_TRAFFIC": "LINK_CLICKS",
        "OUTCOME_SALES": "OFFSITE_CONVERSIONS",
        "OUTCOME_AWARENESS": "REACH",
        "OUTCOME_ENGAGEMENT": "POST_ENGAGEMENT",
    }.get(objective, "LEAD_GENERATION")


TRAFFIC_TOOLS = [
    get_account_info,
    save_account_info,
    list_ad_accounts,
    list_facebook_pages,
    validate_and_create_full_ad,
    get_account_performance,
    analyze_campaign_performance,
    activate_meta_campaign,
    pause_meta_campaign,
    adjust_campaign_budget,
]
