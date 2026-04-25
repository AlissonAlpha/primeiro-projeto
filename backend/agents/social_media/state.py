from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages


class PostData(TypedDict):
    caption: str
    hashtags: List[str]
    image_url: Optional[str]
    video_url: Optional[str]
    platform: str  # "instagram", "facebook", "linkedin"
    scheduled_at: Optional[str]


class SocialMediaState(TypedDict):
    messages: Annotated[list, add_messages]
    brand_voice: Optional[str]
    content_calendar: Optional[List[dict]]
    pending_posts: Optional[List[PostData]]
    published_posts: Optional[List[dict]]
    performance_data: Optional[dict]
    current_step: str
    error: Optional[str]
