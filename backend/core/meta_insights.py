import requests
from datetime import datetime, timedelta
from .config import settings


def _get(path: str, params: dict) -> dict:
    params["access_token"] = settings.META_ACCESS_TOKEN
    r = requests.get(f"https://graph.facebook.com/v21.0{path}", params=params)
    return r.json()


def get_account_insights(ad_account_id: str, days: int = 30) -> dict:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")
    data = _get(f"/{ad_account_id}/insights", {
        "fields": "impressions,clicks,spend,ctr,cpc,cpp,reach,frequency,actions,action_values",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "account",
    })
    return data.get("data", [{}])[0] if data.get("data") else {}


def get_campaigns_with_insights(ad_account_id: str, days: int = 30) -> list[dict]:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")

    # Fetch campaigns
    camps = _get(f"/{ad_account_id}/campaigns", {
        "fields": "id,name,status,objective,daily_budget,created_time",
        "limit": 50,
    })

    campaigns = camps.get("data", [])
    if not campaigns:
        return []

    # Fetch insights for all campaigns at once
    insights_data = _get(f"/{ad_account_id}/insights", {
        "fields": "campaign_id,campaign_name,impressions,clicks,spend,ctr,cpc,reach,actions,action_values",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "level": "campaign",
        "limit": 100,
    })

    insights_map = {}
    for row in insights_data.get("data", []):
        insights_map[row.get("campaign_id", "")] = row

    result = []
    for c in campaigns:
        ins = insights_map.get(c["id"], {})
        leads = sum(
            int(a.get("value", 0))
            for a in ins.get("actions", [])
            if a.get("action_type") in ("lead", "onsite_conversion.lead_grouped")
        )
        spend = float(ins.get("spend", 0))
        clicks = int(ins.get("clicks", 0))
        cpl = round(spend / leads, 2) if leads > 0 else None

        result.append({
            "id": c["id"],
            "name": c["name"],
            "status": c["status"],
            "objective": c.get("objective", ""),
            "daily_budget_brl": round(int(c.get("daily_budget", 0)) / 100, 2),
            "created_time": c.get("created_time", ""),
            "insights": {
                "impressions": int(ins.get("impressions", 0)),
                "clicks": clicks,
                "spend_brl": spend,
                "ctr": round(float(ins.get("ctr", 0)), 2),
                "cpc_brl": round(float(ins.get("cpc", 0)), 2),
                "reach": int(ins.get("reach", 0)),
                "leads": leads,
                "cpl_brl": cpl,
            },
        })

    return result


def get_campaign_insights_detail(campaign_id: str, days: int = 7) -> dict:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")
    data = _get(f"/{campaign_id}/insights", {
        "fields": "impressions,clicks,spend,ctr,cpc,reach,frequency,actions,action_values",
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "time_increment": 1,
    })
    return {"campaign_id": campaign_id, "days": days, "data": data.get("data", [])}


def activate_campaign(campaign_id: str) -> dict:
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{campaign_id}",
        params={"access_token": settings.META_ACCESS_TOKEN},
        json={"status": "ACTIVE"},
    )
    return r.json()


def pause_campaign_api(campaign_id: str) -> dict:
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{campaign_id}",
        params={"access_token": settings.META_ACCESS_TOKEN},
        json={"status": "PAUSED"},
    )
    return r.json()


def update_campaign_budget(campaign_id: str, new_daily_budget_brl: float) -> dict:
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{campaign_id}",
        params={"access_token": settings.META_ACCESS_TOKEN},
        json={"daily_budget": int(new_daily_budget_brl * 100)},
    )
    return r.json()
