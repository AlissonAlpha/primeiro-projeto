from langchain_core.tools import tool
from typing import Optional
import structlog
import requests
from core.meta_client import (
    get_all_ad_accounts,
    create_campaign as meta_create_campaign,
    get_campaigns as meta_get_campaigns,
    pause_campaign as meta_pause_campaign,
)
from core.meta_ads_builder import (
    create_ad_set,
    create_ad_creative,
    create_ad,
    build_targeting,
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
def list_ad_accounts() -> dict:
    """List all Meta Ads accounts available. Use this to show accounts and let user choose."""
    try:
        accounts = get_all_ad_accounts()
        active = [a for a in accounts if a["status"] == "Ativo"]
        return {"success": True, "total": len(accounts), "active_count": len(active), "accounts": active}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def list_facebook_pages() -> dict:
    """List all Facebook Pages from all Business Managers. Required to create ad creatives."""
    try:
        token = settings.META_ACCESS_TOKEN
        r = requests.get(
            "https://graph.facebook.com/v21.0/me/businesses",
            params={"fields": "id,name,owned_pages{id,name}", "access_token": token},
        )
        data = r.json()
        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}

        all_pages = []
        for bm in data.get("data", []):
            bm_name = bm.get("name", "")
            for page in bm.get("owned_pages", {}).get("data", []):
                all_pages.append({
                    "id": page["id"],
                    "name": page["name"],
                    "business": bm_name,
                })

        return {"success": True, "pages": all_pages, "total": len(all_pages)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_meta_campaign(
    ad_account_id: str,
    name: str,
    objective: str,
    daily_budget_brl: float,
) -> dict:
    """Create a campaign on Meta Ads (PAUSED).
    objective options: leads, trafego, vendas, awareness, reconhecimento, engajamento"""
    logger.info("creating_meta_campaign", account=ad_account_id, name=name)
    try:
        meta_objective = OBJECTIVE_MAP.get(objective.lower(), "OUTCOME_LEADS")
        result = meta_create_campaign(
            ad_account_id=ad_account_id,
            name=name,
            objective=meta_objective,
            daily_budget_cents=int(daily_budget_brl * 100),
            status="PAUSED",
        )
        return {
            "success": True,
            "campaign_id": result["id"],
            "name": result["name"],
            "objective": meta_objective,
            "daily_budget_brl": daily_budget_brl,
            "status": "PAUSED",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_meta_ad_set(
    ad_account_id: str,
    campaign_id: str,
    name: str,
    daily_budget_brl: float,
    age_min: int,
    age_max: int,
    countries: list[str],
    campaign_objective: str = "OUTCOME_AWARENESS",
    interest_ids: list[str] = [],
    genders: list[int] = [],
) -> dict:
    """Create an Ad Set inside a campaign with audience targeting.
    genders: 1=masculino, 2=feminino. Leave empty for all genders.
    countries: list of country codes, e.g. ['BR']
    interest_ids: Meta interest IDs (leave empty for broad targeting)"""
    logger.info("creating_ad_set", campaign_id=campaign_id, name=name)
    try:
        targeting = build_targeting(
            age_min=age_min,
            age_max=age_max,
            genders=genders if genders else None,
            geo_locations={"countries": countries},
            interests=[{"id": i} for i in interest_ids] if interest_ids else None,
        )
        result = create_ad_set(
            ad_account_id=ad_account_id,
            campaign_id=campaign_id,
            name=name,
            daily_budget_cents=int(daily_budget_brl * 100),
            targeting=targeting,
            campaign_objective=campaign_objective,
            status="PAUSED",
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_meta_ad_creative(
    ad_account_id: str,
    page_id: str,
    name: str,
    primary_text: str,
    headline: str,
    description: str,
    cta_button: str,
    link_url: str,
    image_url: str = "",
) -> dict:
    """Create an Ad Creative (copy + image) for Meta Ads.
    cta_button options: LEARN_MORE, SIGN_UP, SHOP_NOW, CONTACT_US, GET_QUOTE
    image_url: public URL of the image (from Supabase Storage upload). Leave empty to use text-only."""
    logger.info("creating_ad_creative", name=name, page_id=page_id)
    try:
        token = settings.META_ACCESS_TOKEN

        # Build object_story_spec
        link_data = {
            "link": link_url,
            "message": primary_text,
            "name": headline,
            "description": description,
            "call_to_action": {
                "type": cta_button,
                "value": {"link": link_url},
            },
        }

        # Add image if provided
        if image_url:
            link_data["picture"] = image_url

        r = requests.post(
            f"https://graph.facebook.com/v21.0/{ad_account_id}/adcreatives",
            params={"access_token": token},
            json={
                "name": name,
                "object_story_spec": {
                    "page_id": page_id,
                    "link_data": link_data,
                },
            },
        )
        data = r.json()
        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}
        return {"success": True, "creative_id": data["id"], "name": name}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_meta_ad(
    ad_account_id: str,
    ad_set_id: str,
    creative_id: str,
    name: str,
) -> dict:
    """Create the final Ad linking an Ad Set to a Creative. The ad starts PAUSED."""
    logger.info("creating_ad", name=name, ad_set_id=ad_set_id)
    try:
        token = settings.META_ACCESS_TOKEN
        r = requests.post(
            f"https://graph.facebook.com/v21.0/{ad_account_id}/ads",
            params={"access_token": token},
            json={
                "name": name,
                "adset_id": ad_set_id,
                "creative": {"creative_id": creative_id},
                "status": "PAUSED",
            },
        )
        data = r.json()
        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}
        return {
            "success": True,
            "ad_id": data["id"],
            "name": name,
            "status": "PAUSED",
            "message": f"Anúncio criado com sucesso! ID: {data['id']}. Pronto para revisão e ativação.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def list_campaigns(ad_account_id: str) -> dict:
    """List all campaigns in a Meta Ads account."""
    try:
        campaigns = meta_get_campaigns(ad_account_id)
        return {"success": True, "ad_account_id": ad_account_id, "total": len(campaigns), "campaigns": campaigns}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def pause_meta_campaign(campaign_id: str) -> dict:
    """Pause an active Meta Ads campaign."""
    try:
        result = meta_pause_campaign(campaign_id)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


TRAFFIC_TOOLS = [
    list_ad_accounts,
    list_facebook_pages,
    create_meta_campaign,
    create_meta_ad_set,
    create_meta_ad_creative,
    create_meta_ad,
    list_campaigns,
    pause_meta_campaign,
]
