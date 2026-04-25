from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage
from .state import SocialMediaState
from .tools import SOCIAL_MEDIA_TOOLS
from backend.core.llm import get_claude


SYSTEM_PROMPT = """You are an expert social media manager specialized in creating engaging content
that builds brand awareness and drives conversions. Your expertise covers:

1. Content strategy and editorial calendar planning
2. Writing compelling captions optimized per platform:
   - Instagram: visual storytelling, emotional hooks, strategic hashtags
   - Facebook: community engagement, longer narratives
   - LinkedIn: professional authority, thought leadership
3. Hashtag research and optimization
4. Best posting times per audience and platform
5. Community management tone and engagement
6. Performance analysis and content iteration

Your content always:
- Reflects the brand voice consistently
- Includes a clear Call-To-Action (CTA)
- Uses platform-native formats and trends
- Is SEO-friendly for social search

Respond in the same language the user writes to you."""


def should_continue(state: SocialMediaState) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def call_model(state: SocialMediaState) -> dict:
    llm = get_claude()
    llm_with_tools = llm.bind_tools(SOCIAL_MEDIA_TOOLS)

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)

    return {"messages": [response], "current_step": "model_called"}


def build_social_media_graph():
    tool_node = ToolNode(SOCIAL_MEDIA_TOOLS)

    graph = StateGraph(SocialMediaState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    return graph.compile()


social_media_agent = build_social_media_graph()
