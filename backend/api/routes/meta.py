from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.meta_client import get_all_ad_accounts, create_campaign
from core.meta_insights import (
    get_campaigns_with_insights,
    get_campaign_insights_detail,
    activate_campaign,
    pause_campaign_api,
    update_campaign_budget,
)

router = APIRouter(prefix="/meta", tags=["meta-ads"])


@router.get("/accounts")
async def list_accounts():
    try:
        accounts = get_all_ad_accounts()
        return {"accounts": accounts, "total": len(accounts)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/accounts/{ad_account_id}/campaigns")
async def list_campaigns(ad_account_id: str, days: int = 30):
    try:
        campaigns = get_campaigns_with_insights(ad_account_id, days)
        active = [c for c in campaigns if c["status"] == "ACTIVE"]
        total_spend = sum(c["insights"]["spend_brl"] for c in campaigns)
        total_leads = sum(c["insights"]["leads"] for c in campaigns)
        return {
            "campaigns": campaigns,
            "total": len(campaigns),
            "active_count": len(active),
            "total_spend_brl": round(total_spend, 2),
            "total_leads": total_leads,
            "period_days": days,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/accounts/{ad_account_id}/campaigns/{campaign_id}/insights")
async def campaign_insights(ad_account_id: str, campaign_id: str, days: int = 7):
    try:
        return get_campaign_insights_detail(campaign_id, days)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.patch("/campaigns/{campaign_id}/activate")
async def activate(campaign_id: str):
    try:
        result = activate_campaign(campaign_id)
        if "error" in result:
            raise HTTPException(400, result["error"]["message"])
        return {"success": True, "campaign_id": campaign_id, "status": "ACTIVE"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.patch("/campaigns/{campaign_id}/pause")
async def pause(campaign_id: str):
    try:
        result = pause_campaign_api(campaign_id)
        if "error" in result:
            raise HTTPException(400, result["error"]["message"])
        return {"success": True, "campaign_id": campaign_id, "status": "PAUSED"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


class BudgetUpdate(BaseModel):
    daily_budget_brl: float


@router.patch("/campaigns/{campaign_id}/budget")
async def update_budget(campaign_id: str, body: BudgetUpdate):
    try:
        result = update_campaign_budget(campaign_id, body.daily_budget_brl)
        if "error" in result:
            raise HTTPException(400, result["error"]["message"])
        return {"success": True, "campaign_id": campaign_id, "daily_budget_brl": body.daily_budget_brl}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
