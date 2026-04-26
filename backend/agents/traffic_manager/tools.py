from langchain_core.tools import tool
from typing import Optional
import structlog
import requests
from core.meta_client import get_all_ad_accounts
from core.account_settings import get_account_settings_sync, save_account_settings_sync
from core.meta_insights import (
    get_campaigns_with_insights,
    get_campaign_insights_detail,
    activate_campaign,
    pause_campaign_api,
    update_campaign_budget,
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

PROMOTED_OBJECT_MAP = {
    "OUTCOME_LEADS": "page_id",
    "OUTCOME_TRAFFIC": "page_id",
    "OUTCOME_SALES": "page_id",
    "OUTCOME_ENGAGEMENT": "page_id",
}


def _get_optimization_goal(objective: str) -> str:
    return {
        "OUTCOME_LEADS": "LEAD_GENERATION",
        "OUTCOME_TRAFFIC": "LINK_CLICKS",
        "OUTCOME_SALES": "OFFSITE_CONVERSIONS",
        "OUTCOME_AWARENESS": "REACH",
        "OUTCOME_ENGAGEMENT": "POST_ENGAGEMENT",
    }.get(objective, "LEAD_GENERATION")


# ─────────────────────────────────────────────
# DISCOVERY TOOLS
# ─────────────────────────────────────────────

@tool
def list_ad_accounts() -> dict:
    """List all active Meta Ads accounts available."""
    try:
        accounts = get_all_ad_accounts()
        active = [a for a in accounts if a["status"] == "Ativo"]
        return {"success": True, "active_count": len(active), "accounts": active}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def list_facebook_pages() -> dict:
    """List all Facebook Pages from all Business Managers."""
    try:
        r = requests.get("https://graph.facebook.com/v21.0/me/businesses",
            params={"fields": "id,name,owned_pages{id,name}", "access_token": settings.META_ACCESS_TOKEN})
        all_pages = []
        for bm in r.json().get("data", []):
            for page in bm.get("owned_pages", {}).get("data", []):
                all_pages.append({"id": page["id"], "name": page["name"], "business": bm.get("name", "")})
        return {"success": True, "pages": all_pages, "total": len(all_pages)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def search_locations(query: str, country_code: str = "BR") -> dict:
    """Search Meta Ads location keys by city/region name.
    Call this whenever user mentions a specific city or region."""
    try:
        r = requests.get("https://graph.facebook.com/v21.0/search",
            params={"type": "adgeolocation", "q": query, "country_code": country_code,
                    "access_token": settings.META_ACCESS_TOKEN, "limit": 8})
        data = r.json()
        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}
        locations = [
            {"key": l["key"], "name": l["name"], "type": l["type"],
             "region": l.get("region", ""), "country": l.get("country_name", "")}
            for l in data.get("data", []) if l.get("type") in ("city", "region", "country")
        ]
        return {"success": True, "query": query, "locations": locations}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def search_interests(query: str) -> dict:
    """Search Meta Ads interest IDs by keyword for manual audience targeting.
    Use this when user wants to target specific interests (e.g., 'motos', 'fitness', 'moda').
    Returns interest IDs to use in audience targeting."""
    try:
        r = requests.get("https://graph.facebook.com/v21.0/search",
            params={"type": "adinterest", "q": query, "locale": "pt_BR",
                    "access_token": settings.META_ACCESS_TOKEN, "limit": 10})
        data = r.json()
        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}
        interests = [
            {"id": i["id"], "name": i["name"],
             "audience_size": i.get("audience_size_lower_bound", 0),
             "path": " > ".join(i.get("path", []))}
            for i in data.get("data", [])
        ]
        return {"success": True, "query": query, "interests": interests}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_account_info(ad_account_id: str) -> dict:
    """Get saved settings for an ad account: WhatsApp, website, page ID.
    Always call this after user selects an account."""
    try:
        cfg = get_account_settings_sync(ad_account_id)
        if not cfg:
            return {"success": True, "found": False, "ad_account_id": ad_account_id}
        wa = cfg.get("whatsapp_number")
        return {
            "success": True, "found": True,
            "ad_account_id": ad_account_id,
            "account_name": cfg.get("account_name"),
            "whatsapp_number": wa,
            "whatsapp_url": f"https://wa.me/{wa}" if wa else None,
            "website_url": cfg.get("website_url"),
            "facebook_page_id": cfg.get("facebook_page_id"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def save_account_info(ad_account_id: str, account_name: str,
                      whatsapp_number: str = "", website_url: str = "",
                      facebook_page_id: str = "") -> dict:
    """Save account settings for future use."""
    try:
        result = save_account_settings_sync(
            ad_account_id=ad_account_id, account_name=account_name,
            whatsapp_number=whatsapp_number or None,
            website_url=website_url or None,
            facebook_page_id=facebook_page_id or None,
        )
        return {"success": True, "saved": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────
# CAMPAIGN CREATION
# ─────────────────────────────────────────────

@tool
def create_complete_campaign(
    ad_account_id: str,
    campaign_name: str,
    objective: str,
    page_id: str,
    link_url: str,
    ad_sets: list[dict],
    budget_type: str = "ABO",
    campaign_daily_budget_brl: float = 0,
    activate_immediately: bool = True,
) -> dict:
    """Create a complete campaign with multiple ad sets and multiple creatives per ad set.

    budget_type: 'ABO' (budget per ad set) or 'CBO' (campaign-level budget)
    campaign_daily_budget_brl: required only for CBO
    activate_immediately: True = ACTIVE, False = PAUSED

    ad_sets format (list of dicts):
    [
      {
        "name": "Conjunto 01 — Público Jovem",
        "daily_budget_brl": 30.0,        # required for ABO, ignored for CBO
        "age_min": 18,
        "age_max": 35,
        "genders": [],                    # [] = all, [1] = male, [2] = female
        "city_keys": ["244475"],          # from search_locations
        "city_radius_km": 30,
        "countries": ["BR"],              # fallback if no city_keys
        "audience_type": "advantage",     # "advantage" or "manual"
        "interest_ids": [],               # from search_interests (only for manual)
        "creatives": [
          {
            "primary_text": "Texto do anúncio...",
            "headline": "Headline aqui",
            "cta_button": "LEARN_MORE",
            "image_url": ""
          }
        ]
      }
    ]
    """
    token = settings.META_ACCESS_TOKEN
    meta_objective = OBJECTIVE_MAP.get(objective.lower(), "OUTCOME_LEADS")
    status = "ACTIVE" if activate_immediately else "PAUSED"

    # Validation
    issues = []
    if not ad_sets:
        issues.append("Nenhum conjunto de anúncios fornecido.")
    for i, ads in enumerate(ad_sets):
        if not ads.get("creatives"):
            issues.append(f"Conjunto {i+1} sem criativos.")
        if budget_type == "ABO" and not ads.get("daily_budget_brl"):
            issues.append(f"Conjunto {i+1} sem orçamento (ABO requer orçamento por conjunto).")
        for j, cr in enumerate(ads.get("creatives", [])):
            if len(cr.get("headline", "")) > 40:
                issues.append(f"Conjunto {i+1}, criativo {j+1}: headline muito longa (máx 40 chars).")
    if budget_type == "CBO" and not campaign_daily_budget_brl:
        issues.append("CBO requer orçamento total da campanha.")
    if issues:
        return {"success": False, "validation_failed": True, "issues": issues}

    logger.info("creating_complete_campaign", name=campaign_name,
                ad_sets=len(ad_sets), budget_type=budget_type, status=status)

    try:
        # ── 1. CAMPAIGN ──
        camp_body: dict = {
            "name": campaign_name,
            "objective": meta_objective,
            "status": status,
            "special_ad_categories": [],
        }
        if budget_type == "CBO":
            camp_body["daily_budget"] = int(campaign_daily_budget_brl * 100)
            camp_body["bid_strategy"] = "LOWEST_COST_WITHOUT_CAP"
        else:
            camp_body["is_adset_budget_sharing_enabled"] = False

        camp_r = requests.post(f"https://graph.facebook.com/v21.0/{ad_account_id}/campaigns",
            params={"access_token": token}, json=camp_body)
        camp = camp_r.json()
        if "error" in camp:
            return {"success": False, "step": "campaign", "error": camp["error"]["message"]}
        campaign_id = camp["id"]

        created_ad_sets = []

        # ── 2. AD SETS + CREATIVES + ADS ──
        for idx, ads_cfg in enumerate(ad_sets):
            set_name = ads_cfg.get("name", f"{campaign_name} — Conjunto {idx+1:02d}")

            # Build geo
            if ads_cfg.get("city_keys"):
                radius = ads_cfg.get("city_radius_km", 0)
                if radius > 0:
                    geo = {"cities": [{"key": k, "radius": radius, "distance_unit": "kilometer"}
                                      for k in ads_cfg["city_keys"]]}
                else:
                    geo = {"cities": [{"key": k} for k in ads_cfg["city_keys"]]}
            else:
                geo = {"countries": ads_cfg.get("countries", ["BR"])}

            # Build targeting
            targeting: dict = {
                "age_min": ads_cfg.get("age_min", 18),
                "age_max": ads_cfg.get("age_max", 65),
                "geo_locations": geo,
            }
            if ads_cfg.get("genders"):
                targeting["genders"] = ads_cfg["genders"]

            # Audience type
            if ads_cfg.get("audience_type") == "advantage":
                targeting["targeting_automation"] = {"advantage_audience": 1}
            else:
                targeting["targeting_automation"] = {"advantage_audience": 0}
                if ads_cfg.get("interest_ids"):
                    targeting["flexible_spec"] = [
                        {"interests": [{"id": i} for i in ads_cfg["interest_ids"]]}
                    ]

            # Ad set body
            adset_body: dict = {
                "name": set_name,
                "campaign_id": campaign_id,
                "billing_event": "IMPRESSIONS",
                "optimization_goal": _get_optimization_goal(meta_objective),
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                "targeting": targeting,
                "status": status,
            }
            if budget_type == "ABO":
                adset_body["daily_budget"] = int(ads_cfg["daily_budget_brl"] * 100)
            if meta_objective in PROMOTED_OBJECT_MAP:
                adset_body["promoted_object"] = {"page_id": page_id}

            adset_r = requests.post(f"https://graph.facebook.com/v21.0/{ad_account_id}/adsets",
                params={"access_token": token}, json=adset_body)
            adset = adset_r.json()
            if "error" in adset:
                return {"success": False, "step": f"ad_set_{idx+1}", "error": adset["error"]["message"]}
            adset_id = adset["id"]

            created_creatives = []

            # ── 3. CREATIVES + ADS ──
            for cidx, cr in enumerate(ads_cfg.get("creatives", [])):
                cr_name = f"{set_name} — Criativo {cidx+1:02d}"
                link_data: dict = {
                    "link": link_url,
                    "message": cr.get("primary_text", ""),
                    "name": cr.get("headline", ""),
                    "call_to_action": {
                        "type": cr.get("cta_button", "LEARN_MORE"),
                        "value": {"link": link_url},
                    },
                }
                if cr.get("image_url"):
                    link_data["picture"] = cr["image_url"]

                creative_r = requests.post(f"https://graph.facebook.com/v21.0/{ad_account_id}/adcreatives",
                    params={"access_token": token},
                    json={"name": cr_name, "object_story_spec": {
                        "page_id": page_id, "link_data": link_data}})
                creative = creative_r.json()
                if "error" in creative:
                    return {"success": False, "step": f"creative_{idx+1}_{cidx+1}",
                            "error": creative["error"]["message"]}
                creative_id = creative["id"]

                ad_r = requests.post(f"https://graph.facebook.com/v21.0/{ad_account_id}/ads",
                    params={"access_token": token},
                    json={"name": cr_name, "adset_id": adset_id,
                          "creative": {"creative_id": creative_id}, "status": status})
                ad = ad_r.json()
                if "error" in ad:
                    return {"success": False, "step": f"ad_{idx+1}_{cidx+1}",
                            "error": ad["error"]["message"]}

                created_creatives.append({"creative_id": creative_id, "ad_id": ad["id"]})

            created_ad_sets.append({
                "name": set_name, "adset_id": adset_id,
                "creatives_count": len(created_creatives),
                "creatives": created_creatives,
            })

        total_ads = sum(s["creatives_count"] for s in created_ad_sets)
        return {
            "success": True,
            "status": status,
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "budget_type": budget_type,
            "ad_sets_created": len(created_ad_sets),
            "total_ads_created": total_ads,
            "ad_sets": created_ad_sets,
            "message": f"✅ {len(created_ad_sets)} conjunto(s) × {total_ads} anúncio(s) criados — {'ATIVOS' if activate_immediately else 'PAUSADOS'}!",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────
# MONITORING & OPTIMIZATION TOOLS
# ─────────────────────────────────────────────

@tool
def get_account_performance(ad_account_id: str, days: int = 30) -> dict:
    """Get overall account performance metrics."""
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
            "success": True, "period_days": days,
            "summary": {
                "active_campaigns": len(active), "total_campaigns": len(campaigns),
                "total_spend_brl": round(total_spend, 2),
                "total_impressions": total_impressions, "total_clicks": total_clicks,
                "total_leads": total_leads, "avg_ctr_pct": avg_ctr, "avg_cpl_brl": avg_cpl,
            },
            "campaigns": campaigns,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def analyze_campaign_performance(campaign_id: str, days: int = 7) -> dict:
    """Analyze campaign with diagnosis and optimization recommendations."""
    try:
        data = get_campaign_insights_detail(campaign_id, days)
        rows = data.get("data", [])
        if not rows:
            return {"success": True, "campaign_id": campaign_id,
                    "message": "Sem dados no período — campanha muito nova ou sem veiculação."}
        total_spend = sum(float(r.get("spend", 0)) for r in rows)
        total_impressions = sum(int(r.get("impressions", 0)) for r in rows)
        total_clicks = sum(int(r.get("clicks", 0)) for r in rows)
        total_leads = sum(
            int(a.get("value", 0)) for r in rows for a in r.get("actions", [])
            if a.get("action_type") in ("lead", "onsite_conversion.lead_grouped"))
        avg_ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions else 0
        avg_cpc = round(total_spend / total_clicks, 2) if total_clicks else 0
        cpl = round(total_spend / total_leads, 2) if total_leads else None

        diagnosis, recommendations = [], []
        if avg_ctr < 0.5:
            diagnosis.append("⚠️ CTR muito baixo (< 0.5%) — criativo não está chamando atenção.")
            recommendations.append("Teste novo criativo com imagem mais impactante ou hook diferente.")
        elif avg_ctr >= 2.0:
            diagnosis.append("✅ CTR excelente (≥ 2%).")
        if avg_cpc > 5:
            diagnosis.append(f"⚠️ CPC alto (R${avg_cpc}) — custo por clique acima do ideal.")
            recommendations.append("Refine o público ou aumente o orçamento para ganhar escala.")
        if total_impressions < 1000 and days >= 3:
            diagnosis.append("⚠️ Alcance muito baixo — público restrito ou orçamento insuficiente.")
            recommendations.append("Amplie a faixa etária ou aumente o orçamento diário.")
        if cpl and cpl > 50:
            diagnosis.append(f"⚠️ CPL alto (R${cpl}).")
            recommendations.append("Revise o formulário de leads ou a oferta do anúncio.")
        elif cpl and cpl <= 20:
            diagnosis.append(f"✅ CPL excelente (R${cpl}).")
        if not diagnosis:
            diagnosis.append("📊 Campanha em fase de aprendizado — aguarde mais dados.")

        return {
            "success": True, "campaign_id": campaign_id, "period_days": days,
            "metrics": {"spend_brl": round(total_spend, 2), "impressions": total_impressions,
                        "clicks": total_clicks, "ctr_pct": avg_ctr, "cpc_brl": avg_cpc,
                        "leads": total_leads, "cpl_brl": cpl},
            "diagnosis": diagnosis, "recommendations": recommendations,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def activate_meta_campaign(campaign_id: str) -> dict:
    """Activate a paused Meta Ads campaign."""
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
    """Adjust daily budget of a campaign."""
    try:
        result = update_campaign_budget(campaign_id, new_daily_budget_brl)
        if "error" in result:
            return {"success": False, "error": result["error"]["message"]}
        return {"success": True, "campaign_id": campaign_id,
                "new_daily_budget_brl": new_daily_budget_brl, "reason": reason}
    except Exception as e:
        return {"success": False, "error": str(e)}


TRAFFIC_TOOLS = [
    search_locations,
    search_interests,
    get_account_info,
    save_account_info,
    list_ad_accounts,
    list_facebook_pages,
    create_complete_campaign,
    get_account_performance,
    analyze_campaign_performance,
    activate_meta_campaign,
    pause_meta_campaign,
    adjust_campaign_budget,
]
