from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from core.llm import get_claude
from core.freepik_client import generate_image_sync
from core.storage import upload_creative
import asyncio
import structlog

logger = structlog.get_logger()


class ImageCreatorState(TypedDict):
    messages: Annotated[list, add_messages]
    brief: Optional[dict]
    generated_images: Optional[list]
    current_step: str


@tool
def generate_image_from_brief(
    prompt: str,
    aspect_ratio: str = "square_1_1",
    style: str = "photo",
    variation: int = 1,
) -> dict:
    """Generate an image using Freepik API based on a creative brief prompt.

    aspect_ratio options:
    - square_1_1 → Feed Instagram/Facebook (1:1)
    - portrait_4_5 → Feed Instagram otimizado (4:5)
    - portrait_9_16 → Stories/Reels (9:16)
    - landscape_16_9 → YouTube/Facebook cover (16:9)

    style options: photo, digital-art, illustration, 3d, painting

    variation: generate multiple variations (1, 2, 3) by calling multiple times"""
    logger.info("generating_image", style=style, aspect_ratio=aspect_ratio)
    result = generate_image_sync(prompt, aspect_ratio, style)
    if result.get("success"):
        return {
            "success": True,
            "image_url": result.get("stored_url") or result.get("image_url") or result.get("freepik_url"),
            "variation": variation,
            "aspect_ratio": aspect_ratio,
            "style": style,
            "provider": "freepik",
        }
    return result


@tool
def optimize_prompt_for_freepik(
    original_prompt: str,
    segment: str,
    emotion: str,
    platform: str,
) -> dict:
    """Optimize a visual direction description into an effective Freepik/Mystic prompt.
    Always call this before generate_image_from_brief to get the best results."""
    aspect_map = {
        "instagram": "portrait_2_3",
        "stories": "social_story_9_16",
        "reels": "social_story_9_16",
        "facebook": "square_1_1",
        "linkedin": "widescreen_16_9",
        "feed": "portrait_2_3",
    }
    aspect = aspect_map.get(platform.lower(), "square_1_1")

    optimized = (
        f"{original_prompt}, "
        f"professional commercial photography, "
        f"shot for {platform} marketing in Brazil, "
        f"emotion: {emotion}, "
        f"segment: {segment}, "
        f"highly detailed, sharp focus, vibrant and engaging, "
        f"natural lighting, authentic Brazilian people and environments, "
        f"no text, no watermarks, advertising quality"
    )
    return {
        "success": True,
        "optimized_prompt": optimized,
        "recommended_aspect_ratio": aspect,
        "recommended_style": "photo",
    }


IMAGE_CREATOR_TOOLS = [optimize_prompt_for_freepik, generate_image_from_brief]


SYSTEM_PROMPT = """Você é o Criador de Imagens da Agência do Futuro IA.
Especialista em criar visuais impactantes para marketing digital usando IA generativa.

## SEU FLUXO

Quando receber um Brief Criativo ou solicitação de imagem:

1. Use `optimize_prompt_for_freepik` para otimizar o prompt recebido
2. Use `generate_image_from_brief` para gerar a imagem
3. Se pedido múltiplas variações, gere cada uma com `variation=1`, `variation=2`, etc.
4. Apresente os resultados com as URLs das imagens geradas

## ASPECT RATIOS POR USO

| Formato | Ratio | Quando usar |
|---------|-------|-------------|
| Feed Instagram | portrait_4_5 | Posts normais no feed |
| Stories/Reels | portrait_9_16 | Stories, Reels, TikTok |
| Feed Facebook | square_1_1 | Posts no Facebook |
| LinkedIn | landscape_16_9 | Posts profissionais |

## ESTILOS DISPONÍVEIS
- `photo` — fotorrealista (melhor para anúncios e produtos)
- `digital-art` — arte digital (bom para brands jovens)
- `illustration` — ilustração (bom para infográficos)
- `3d` — render 3D (bom para produtos)

## DICAS DE QUALIDADE
- Sempre especifique que é fotografia comercial profissional
- Mencione o contexto brasileiro (pessoas, ambiente, cultura)
- Evite prompts com texto — o Freepik não gera texto bem
- Para anúncios, prefira `photo` com iluminação natural

Responda sempre em português brasileiro."""


def should_continue(state: ImageCreatorState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def call_model(state: ImageCreatorState) -> dict:
    llm = get_claude()
    llm_with_tools = llm.bind_tools(IMAGE_CREATOR_TOOLS)
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "current_step": "image_creator_responded"}


def build_image_creator_graph():
    tool_node = ToolNode(IMAGE_CREATOR_TOOLS)
    graph = StateGraph(ImageCreatorState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")
    return graph.compile()


image_creator_agent = build_image_creator_graph()
