from langchain_core.tools import tool
from typing import Optional
import structlog

logger = structlog.get_logger()


@tool
def generate_post_caption(
    topic: str,
    brand_voice: str,
    platform: str,
    include_cta: bool = True,
) -> dict:
    """Generate an engaging post caption optimized for the target platform."""
    logger.info("generating_caption", topic=topic, platform=platform)
    return {
        "status": "requires_llm",
        "topic": topic,
        "platform": platform,
        "message": "Caption generation handled by LLM chain.",
    }


@tool
def generate_hashtags(topic: str, platform: str, count: int = 20) -> dict:
    """Generate relevant and trending hashtags for a post."""
    return {
        "status": "requires_llm",
        "topic": topic,
        "platform": platform,
        "requested_count": count,
    }


@tool
def schedule_post(
    caption: str,
    platform: str,
    scheduled_at: str,
    image_url: Optional[str] = None,
    hashtags: Optional[list[str]] = None,
) -> dict:
    """Schedule a post to be published at a specific date and time."""
    logger.info("scheduling_post", platform=platform, scheduled_at=scheduled_at)
    return {
        "status": "pending_credentials",
        "platform": platform,
        "scheduled_at": scheduled_at,
        "message": f"Social media API credentials required for {platform}.",
    }


@tool
def get_post_performance(post_id: str, platform: str) -> dict:
    """Get performance metrics for a published post (likes, reach, saves, comments)."""
    return {
        "status": "pending_credentials",
        "post_id": post_id,
        "platform": platform,
        "message": "API credentials required to fetch post performance.",
    }


@tool
def create_content_calendar(
    brand: str,
    niche: str,
    posting_frequency: int,
    month: str,
    platforms: list[str],
) -> dict:
    """Create a full monthly content calendar with post ideas and optimal posting times."""
    logger.info("creating_content_calendar", brand=brand, month=month)
    return {
        "status": "requires_llm",
        "brand": brand,
        "niche": niche,
        "posting_frequency": posting_frequency,
        "month": month,
        "platforms": platforms,
    }


SOCIAL_MEDIA_TOOLS = [
    generate_post_caption,
    generate_hashtags,
    schedule_post,
    get_post_performance,
    create_content_calendar,
]
