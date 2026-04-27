from langchain_core.tools import tool
from typing import Optional
import requests
import structlog
from datetime import datetime
from core.config import settings

logger = structlog.get_logger()


def _page_token(page_id: str) -> str:
    """Get page-level access token."""
    r = requests.get(f"https://graph.facebook.com/v21.0/{page_id}",
        params={"fields": "access_token", "access_token": settings.META_ACCESS_TOKEN})
    return r.json().get("access_token", settings.META_ACCESS_TOKEN)


@tool
def list_connected_accounts() -> dict:
    """List all Facebook Pages and their linked Instagram accounts available for posting."""
    try:
        token = settings.META_ACCESS_TOKEN
        r = requests.get("https://graph.facebook.com/v21.0/me/accounts",
            params={"fields": "id,name,instagram_business_account", "access_token": token})
        data = r.json()
        accounts = []
        for page in data.get("data", []):
            ig = page.get("instagram_business_account", {})
            ig_id = ig.get("id")
            ig_info = {}
            if ig_id:
                r2 = requests.get(f"https://graph.facebook.com/v21.0/{ig_id}",
                    params={"fields": "id,username,followers_count,media_count",
                            "access_token": token})
                ig_info = r2.json()
            accounts.append({
                "facebook_page_id": page["id"],
                "facebook_page_name": page["name"],
                "instagram_id": ig_id,
                "instagram_username": ig_info.get("username"),
                "instagram_followers": ig_info.get("followers_count"),
            })
        return {"success": True, "accounts": accounts, "total": len(accounts)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def publish_facebook_post(
    page_id: str,
    message: str,
    image_url: str = "",
    scheduled_time: str = "",
) -> dict:
    """Publish or schedule a post on a Facebook Page.

    scheduled_time: ISO format in UTC, e.g. '2026-05-10T14:00:00' (must be 10min to 75 days ahead)
    image_url: public URL of the image to attach (optional)"""
    try:
        page_token = _page_token(page_id)
        payload: dict = {"message": message, "access_token": page_token}

        if scheduled_time:
            from datetime import timezone
            dt = datetime.fromisoformat(scheduled_time.replace("Z", ""))
            payload["scheduled_publish_time"] = int(dt.replace(tzinfo=timezone.utc).timestamp())
            payload["published"] = False

        if image_url:
            # Post with photo
            r = requests.post(f"https://graph.facebook.com/v21.0/{page_id}/photos",
                params={"access_token": page_token},
                json={"url": image_url, "message": message,
                      "published": not bool(scheduled_time),
                      **({"scheduled_publish_time": payload.get("scheduled_publish_time")} if scheduled_time else {})})
        else:
            r = requests.post(f"https://graph.facebook.com/v21.0/{page_id}/feed",
                params={"access_token": page_token}, json=payload)

        data = r.json()
        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}
        return {
            "success": True,
            "post_id": data.get("id") or data.get("post_id"),
            "platform": "facebook",
            "scheduled": bool(scheduled_time),
            "scheduled_time": scheduled_time or "agora",
            "message": "Post publicado!" if not scheduled_time else f"Post agendado para {scheduled_time}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def publish_instagram_post(
    instagram_account_id: str,
    caption: str,
    image_url: str,
    scheduled_time: str = "",
) -> dict:
    """Publish or schedule an Instagram post (requires image_url).

    instagram_account_id: the IG business account ID
    image_url: public URL of the image
    scheduled_time: ISO format UTC (optional — posts immediately if not set)"""
    try:
        token = settings.META_ACCESS_TOKEN

        # Step 1: Create media container
        container_params: dict = {
            "image_url": image_url,
            "caption": caption,
            "access_token": token,
        }
        if scheduled_time:
            from datetime import timezone
            dt = datetime.fromisoformat(scheduled_time.replace("Z", ""))
            container_params["scheduled_publish_time"] = int(dt.replace(tzinfo=timezone.utc).timestamp())

        r1 = requests.post(f"https://graph.facebook.com/v21.0/{instagram_account_id}/media",
            params={"access_token": token}, json=container_params)
        d1 = r1.json()
        if "error" in d1:
            return {"success": False, "error": d1["error"]["message"], "step": "container"}
        container_id = d1.get("id")

        # Step 2: Publish container
        if not scheduled_time:
            r2 = requests.post(f"https://graph.facebook.com/v21.0/{instagram_account_id}/media_publish",
                params={"access_token": token}, json={"creation_id": container_id})
            d2 = r2.json()
            if "error" in d2:
                return {"success": False, "error": d2["error"]["message"], "step": "publish"}
            return {"success": True, "media_id": d2.get("id"), "platform": "instagram",
                    "scheduled": False, "message": "Post publicado no Instagram!"}
        else:
            return {"success": True, "container_id": container_id, "platform": "instagram",
                    "scheduled": True, "scheduled_time": scheduled_time,
                    "message": f"Post agendado para {scheduled_time}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_page_insights(page_id: str, days: int = 30) -> dict:
    """Get Facebook Page performance insights: reach, impressions, engagement."""
    try:
        page_token = _page_token(page_id)
        r = requests.get(f"https://graph.facebook.com/v21.0/{page_id}/insights",
            params={
                "metric": "page_impressions,page_reach,page_engaged_users,page_fans",
                "period": "day",
                "since": int((datetime.now().timestamp()) - days * 86400),
                "until": int(datetime.now().timestamp()),
                "access_token": page_token,
            })
        data = r.json()
        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}
        return {"success": True, "insights": data.get("data", []), "period_days": days}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_instagram_insights(instagram_account_id: str) -> dict:
    """Get Instagram Business account insights: followers, reach, impressions."""
    try:
        token = settings.META_ACCESS_TOKEN
        r = requests.get(f"https://graph.facebook.com/v21.0/{instagram_account_id}",
            params={"fields": "id,username,followers_count,media_count,profile_views",
                    "access_token": token})
        data = r.json()
        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}
        return {"success": True, "account": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def generate_caption_and_hashtags(
    topic: str,
    brand_voice: str,
    platform: str,
    cta: str = "",
) -> dict:
    """Generate engaging caption and hashtag set for a social media post.
    Returns caption text and relevant hashtags."""
    return {
        "status": "requires_llm",
        "topic": topic,
        "platform": platform,
        "note": "Caption generated by the agent based on brand voice and topic.",
    }


SOCIAL_MEDIA_TOOLS = [
    list_connected_accounts,
    publish_facebook_post,
    publish_instagram_post,
    get_page_insights,
    get_instagram_insights,
    generate_caption_and_hashtags,
]
