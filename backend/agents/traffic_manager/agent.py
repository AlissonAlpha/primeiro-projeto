from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from .state import TrafficManagerState
from .tools import TRAFFIC_TOOLS
from backend.core.llm import get_claude


SYSTEM_PROMPT = """You are an expert digital marketing traffic manager with deep knowledge of
Meta Ads (Facebook/Instagram) and Google Ads. Your role is to:

1. Create high-performance ad campaigns based on client objectives
2. Monitor campaign KPIs: CTR, CPC, CPM, ROAS, Conversion Rate
3. Optimize budgets and bids to maximize ROI
4. Pause underperforming campaigns and scale winning ones
5. Generate clear performance reports with actionable insights

Always think strategically. Before creating any campaign, confirm:
- Campaign objective (awareness, traffic, leads, sales)
- Target audience (age, location, interests, behaviors)
- Daily/total budget
- Campaign duration
- Platforms (Meta, Google, or both)

Respond in the same language the user writes to you."""


def should_continue(state: TrafficManagerState) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def call_model(state: TrafficManagerState) -> dict:
    llm = get_claude()
    llm_with_tools = llm.bind_tools(TRAFFIC_TOOLS)

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)

    return {"messages": [response], "current_step": "model_called"}


def build_traffic_manager_graph():
    tool_node = ToolNode(TRAFFIC_TOOLS)

    graph = StateGraph(TrafficManagerState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    return graph.compile()


traffic_manager_agent = build_traffic_manager_graph()
