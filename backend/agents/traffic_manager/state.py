from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages


class CampaignData(TypedDict):
    name: str
    objective: str
    budget_daily: float
    budget_total: Optional[float]
    start_date: str
    end_date: Optional[str]
    target_audience: dict
    platforms: List[str]  # ["meta", "google"]
    creative_ids: List[str]


class TrafficManagerState(TypedDict):
    messages: Annotated[list, add_messages]
    campaign_data: Optional[CampaignData]
    meta_campaign_id: Optional[str]
    google_campaign_id: Optional[str]
    performance_data: Optional[dict]
    optimization_suggestions: Optional[List[str]]
    current_step: str
    error: Optional[str]
