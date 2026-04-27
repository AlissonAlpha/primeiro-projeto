"""
Content Pipeline Orchestrator
Strategist → Image Creator → Social Media
"""
import asyncio
import structlog
from langchain_core.messages import HumanMessage
from core.content_brief import ContentBrief
from core.freepik_client import generate_image_sync
from core.storage import upload_creative
import httpx

logger = structlog.get_logger()


async def run_content_pipeline(
    brief: ContentBrief,
    client_name: str = "geral",
    num_images: int = 1,
    aspect_ratio: str = "square_1_1",
    style: str = "photo",
) -> dict:
    """
    Full pipeline: Brief → Image Generation → Social Media prep
    Returns complete result with image URLs and social media content.
    """
    logger.info("pipeline_start", brief_id=brief.id, client=client_name)

    results = {
        "brief_id": brief.id,
        "client": client_name,
        "project": brief.theme,
        "status": "running",
        "images": [],
        "social_media": None,
        "errors": [],
    }

    # ── STEP 1: Generate images ──
    from core.freepik_client import generate_and_store
    image_tasks = []
    for i in range(num_images):
        prompt = brief.image_prompt if i == 0 else f"{brief.image_prompt} variation {i+1}"
        image_tasks.append(generate_and_store(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            style=style,
            client_name=client_name,
            project_name=brief.theme,
        ))

    image_results = await asyncio.gather(*image_tasks, return_exceptions=True)

    for i, img_result in enumerate(image_results):
        if isinstance(img_result, Exception):
            results["errors"].append(f"Imagem {i+1}: {str(img_result)}")
        elif img_result.get("success"):
            results["images"].append({
                "index": i + 1,
                "url": img_result.get("stored_url") or img_result.get("freepik_url"),
                "folder": img_result.get("folder", ""),
                "provider": "freepik",
            })
        else:
            results["errors"].append(f"Imagem {i+1}: {img_result.get('error')}")

    if not results["images"]:
        results["status"] = "failed"
        return results

    # ── STEP 2: Generate social media content using Social Media agent ──
    from agents.social_media.agent import social_media_agent

    social_prompt = f"""Com base neste brief criativo, crie o conteúdo para postagem:

SEGMENTO: {brief.segment}
TEMA: {brief.theme}
HOOK: {brief.hook}
EMOÇÃO: {brief.emotion}
PLATAFORMA: {brief.platform}
FORMATO: {brief.format}
DIREÇÃO DE COPY: {brief.copy_direction}
CTA: {brief.cta}
IMAGEM GERADA: {results["images"][0]["url"]}

Crie:
1. Legenda completa para {brief.platform}
2. Lista de hashtags (20-30)
3. Melhor horário para postar
4. Sugestão de stories complementar"""

    social_result = social_media_agent.invoke({
        "messages": [HumanMessage(content=social_prompt)],
        "current_step": "start",
    })

    results["social_media"] = {
        "content": social_result["messages"][-1].content,
        "platform": brief.platform,
        "best_time": brief.best_time,
    }

    results["status"] = "completed"
    logger.info("pipeline_complete", brief_id=brief.id, images=len(results["images"]))
    return results


async def run_pipeline_from_message(
    user_message: str,
    client_name: str = "geral",
    num_images: int = 1,
) -> dict:
    """
    Full auto pipeline from natural language:
    Message → Strategist generates Brief → Image Creator → Social Media
    """
    from agents.content_strategist.agent import content_strategist_agent
    import json, re

    # Step 1: Strategist generates brief
    strat_result = content_strategist_agent.invoke({
        "messages": [HumanMessage(content=user_message)],
        "current_step": "start",
    })
    strat_response = strat_result["messages"][-1].content

    # Extract brief from tool results in message history
    brief_data = None
    for msg in strat_result["messages"]:
        content = msg.content if hasattr(msg, "content") else ""
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and "brief" in str(block):
                    try:
                        brief_data = block.get("brief") or block
                    except Exception:
                        pass
        if isinstance(content, str) and '"image_prompt"' in content:
            try:
                match = re.search(r'\{[^{}]*"image_prompt"[^{}]*\}', content, re.DOTALL)
                if match:
                    brief_data = json.loads(match.group())
            except Exception:
                pass

    if not brief_data:
        # Build minimal brief from strategist response
        brief_data = {
            "segment": client_name,
            "theme": user_message[:60],
            "hook": "",
            "emotion": "inspiração",
            "format": "post feed",
            "platform": "instagram",
            "copy_direction": "copy engajante",
            "visual_direction": "foto profissional",
            "image_prompt": strat_response[:300],
            "cta": "Saiba mais",
        }

    brief = ContentBrief(**brief_data)
    pipeline_result = await run_content_pipeline(brief, client_name, num_images)
    pipeline_result["strategist_response"] = strat_response
    return pipeline_result
