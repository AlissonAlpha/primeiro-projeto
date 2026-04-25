from langchain_core.tools import tool
from typing import Optional
import structlog
from core.meta_client import (
    get_all_ad_accounts,
    create_campaign as meta_create_campaign,
    get_campaigns as meta_get_campaigns,
    pause_campaign as meta_pause_campaign,
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
    """List all Meta Ads accounts available to manage. Use this to show the user their accounts and let them choose which one to use."""
    try:
        accounts = get_all_ad_accounts()
        active = [a for a in accounts if a["status"] == "Ativo"]
        return {
            "success": True,
            "total": len(accounts),
            "active_count": len(active),
            "accounts": accounts,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_meta_campaign(
    ad_account_id: str,
    name: str,
    objective: str,
    daily_budget_brl: float,
    start_paused: bool = True,
) -> dict:
    """Create a real campaign on Meta Ads (Facebook/Instagram).

    Args:
        ad_account_id: The ad account ID (e.g. act_1371009824662047). Use list_ad_accounts to get available accounts.
        name: Campaign name
        objective: Campaign objective in Portuguese (leads, trafego, vendas, awareness, engajamento)
        daily_budget_brl: Daily budget in BRL (e.g. 50.0 for R$50)
        start_paused: If True, campaign starts paused for review before going live
    """
    logger.info("creating_meta_campaign", account=ad_account_id, name=name, objective=objective)
    try:
        meta_objective = OBJECTIVE_MAP.get(objective.lower(), "OUTCOME_LEADS")
        daily_budget_cents = int(daily_budget_brl * 100)
        status = "PAUSED" if start_paused else "ACTIVE"
        result = meta_create_campaign(
            ad_account_id=ad_account_id,
            name=name,
            objective=meta_objective,
            daily_budget_cents=daily_budget_cents,
            status=status,
        )
        return {
            "success": True,
            "campaign_id": result["id"],
            "name": result["name"],
            "status": result["status"],
            "daily_budget_brl": daily_budget_brl,
            "objective": meta_objective,
            "message": f"Campanha criada com sucesso! ID: {result['id']}. Status: {'PAUSADA (aguardando revisão)' if start_paused else 'ATIVA'}",
        }
    except Exception as e:
        logger.error("meta_campaign_error", error=str(e))
        return {"success": False, "error": str(e)}


@tool
def list_campaigns(ad_account_id: str) -> dict:
    """List all campaigns in a Meta Ads account.

    Args:
        ad_account_id: The ad account ID (e.g. act_1371009824662047)
    """
    try:
        campaigns = meta_get_campaigns(ad_account_id)
        return {
            "success": True,
            "ad_account_id": ad_account_id,
            "total": len(campaigns),
            "campaigns": campaigns,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def pause_meta_campaign(campaign_id: str) -> dict:
    """Pause an active Meta Ads campaign.

    Args:
        campaign_id: The campaign ID to pause
    """
    try:
        result = meta_pause_campaign(campaign_id)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_campaign_performance(campaign_id: str, platform: str = "meta") -> dict:
    """Get performance metrics for a campaign (impressions, clicks, CTR, CPC, ROAS)."""
    return {
        "success": False,
        "message": "Métricas em tempo real requerem que a campanha esteja ativa com dados acumulados.",
    }


TRAFFIC_TOOLS = [
    list_ad_accounts,
    create_meta_campaign,
    list_campaigns,
    pause_meta_campaign,
    get_campaign_performance,
]
