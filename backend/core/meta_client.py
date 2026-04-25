from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.user import User
from .config import settings

_initialized = False


def init_meta_api():
    global _initialized
    if not _initialized:
        FacebookAdsApi.init(
            app_id=settings.META_APP_ID,
            app_secret=settings.META_APP_SECRET,
            access_token=settings.META_ACCESS_TOKEN,
        )
        _initialized = True


def get_all_ad_accounts() -> list[dict]:
    init_meta_api()
    me = User(fbid="me")
    accounts = me.get_ad_accounts(fields=["id", "name", "account_status", "currency", "amount_spent", "balance"])
    result = []
    for acc in accounts:
        status_map = {1: "Ativo", 2: "Desativado", 3: "Encerrado", 7: "Arquivado"}
        result.append({
            "id": acc["id"],
            "name": acc.get("name", ""),
            "status": status_map.get(acc.get("account_status", 0), "Desconhecido"),
            "currency": acc.get("currency", "BRL"),
            "amount_spent": acc.get("amount_spent", "0"),
            "balance": acc.get("balance", "0"),
        })
    return result


def create_campaign(
    ad_account_id: str,
    name: str,
    objective: str,
    daily_budget_cents: int,
    status: str = "PAUSED",
) -> dict:
    init_meta_api()
    account = AdAccount(ad_account_id)
    campaign = account.create_campaign(
        fields=[Campaign.Field.id, Campaign.Field.name],
        params={
            Campaign.Field.name: name,
            Campaign.Field.objective: objective,
            Campaign.Field.status: status,
            Campaign.Field.special_ad_categories: [],
            "daily_budget": daily_budget_cents,
        },
    )
    return {"id": campaign["id"], "name": campaign.get("name", name), "status": status}


def get_campaigns(ad_account_id: str) -> list[dict]:
    init_meta_api()
    account = AdAccount(ad_account_id)
    campaigns = account.get_campaigns(
        fields=[
            Campaign.Field.id,
            Campaign.Field.name,
            Campaign.Field.status,
            Campaign.Field.objective,
            Campaign.Field.daily_budget,
            Campaign.Field.created_time,
        ]
    )
    return [
        {
            "id": c["id"],
            "name": c.get("name"),
            "status": c.get("status"),
            "objective": c.get("objective"),
            "daily_budget": c.get("daily_budget"),
            "created_time": c.get("created_time"),
        }
        for c in campaigns
    ]


def pause_campaign(campaign_id: str) -> dict:
    init_meta_api()
    campaign = Campaign(campaign_id)
    campaign.api_update(params={Campaign.Field.status: "PAUSED"})
    return {"id": campaign_id, "status": "PAUSED"}


def resume_campaign(campaign_id: str) -> dict:
    init_meta_api()
    campaign = Campaign(campaign_id)
    campaign.api_update(params={Campaign.Field.status: "ACTIVE"})
    return {"id": campaign_id, "status": "ACTIVE"}
