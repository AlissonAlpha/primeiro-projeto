from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.meta_client import (
    get_all_ad_accounts,
    create_campaign,
    get_campaigns,
    pause_campaign,
    resume_campaign,
)

router = APIRouter(prefix="/meta", tags=["meta-ads"])


class CreateCampaignRequest(BaseModel):
    ad_account_id: str
    name: str
    objective: str  # OUTCOME_LEADS, OUTCOME_TRAFFIC, OUTCOME_SALES, OUTCOME_AWARENESS
    daily_budget_brl: float
    status: str = "PAUSED"


@router.get("/accounts")
async def list_accounts():
    try:
        accounts = get_all_ad_accounts()
        return {"accounts": accounts, "total": len(accounts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{ad_account_id}/campaigns")
async def list_campaigns(ad_account_id: str):
    try:
        campaigns = get_campaigns(ad_account_id)
        return {"campaigns": campaigns, "total": len(campaigns)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns")
async def create_new_campaign(req: CreateCampaignRequest):
    try:
        # Meta Ads usa centavos
        daily_budget_cents = int(req.daily_budget_brl * 100)
        campaign = create_campaign(
            ad_account_id=req.ad_account_id,
            name=req.name,
            objective=req.objective,
            daily_budget_cents=daily_budget_cents,
            status=req.status,
        )
        return {"success": True, "campaign": campaign}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/campaigns/{campaign_id}/pause")
async def pause(campaign_id: str):
    try:
        return pause_campaign(campaign_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/campaigns/{campaign_id}/resume")
async def resume(campaign_id: str):
    try:
        return resume_campaign(campaign_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
