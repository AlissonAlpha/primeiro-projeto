from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from backend.core.llm import get_claude


class CEOState(TypedDict):
    messages: Annotated[list, add_messages]
    active_campaigns: Optional[list]
    monthly_budget: Optional[float]
    kpi_summary: Optional[dict]
    strategic_decisions: Optional[list]
    current_step: str


SYSTEM_PROMPT = """You are the CEO of a cutting-edge AI Marketing Agency. Your role is to:

1. Define the overall marketing strategy for each client
2. Set KPIs and business goals (ROAS, CAC, LTV, brand awareness)
3. Allocate budgets across channels (Meta Ads, Google Ads, Organic Social)
4. Review performance reports from all agents and make strategic decisions
5. Identify growth opportunities and new marketing channels
6. Ensure ROI targets are met across all client accounts

You coordinate with:
- Traffic Manager: campaign creation and optimization
- Social Media Manager: organic content and community growth
- SEO Specialist: organic search visibility
- Content Creator: all content assets
- Designer: visual identity and creatives

Make data-driven decisions. Always prioritize client business results over vanity metrics.
Respond in the same language the user writes to you."""


def call_model(state: CEOState) -> dict:
    llm = get_claude()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response], "current_step": "ceo_responded"}


def build_ceo_graph():
    graph = StateGraph(CEOState)
    graph.add_node("ceo", call_model)
    graph.set_entry_point("ceo")
    graph.add_edge("ceo", END)
    return graph.compile()


ceo_agent = build_ceo_graph()
