from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage
from agents.content_strategist.agent import content_strategist_agent
from agents.image_creator.agent import image_creator_agent
from core.session import get_session, append_messages
from core.content_brief import ContentBrief
import json
import asyncio

router = APIRouter(prefix="/content", tags=["content"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class PipelineRequest(BaseModel):
    message: str
    client_name: str = "geral"
    num_images: int = 1
    session_id: Optional[str] = None


class BriefToImageRequest(BaseModel):
    brief: dict
    client_name: str = "geral"
    num_images: int = 1
    aspect_ratio: str = "square_1_1"
    style: str = "photo"


@router.post("/strategist/chat")
async def chat_strategist(req: ChatRequest):
    try:
        history = get_session(req.session_id) if req.session_id else []
        user_msg = HumanMessage(content=req.message)
        result = content_strategist_agent.invoke({
            "messages": history + [user_msg],
            "current_step": "start",
        })
        ai_response = result["messages"][-1]
        if req.session_id:
            append_messages(req.session_id, [user_msg, AIMessage(content=ai_response.content)])
        return {
            "agent": "content_strategist",
            "response": ai_response.content,
            "session_id": req.session_id,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/image-creator/chat")
async def chat_image_creator(req: ChatRequest):
    try:
        history = get_session(req.session_id) if req.session_id else []
        user_msg = HumanMessage(content=req.message)
        result = image_creator_agent.invoke({
            "messages": history + [user_msg],
            "current_step": "start",
        })
        ai_response = result["messages"][-1]
        if req.session_id:
            append_messages(req.session_id, [user_msg, AIMessage(content=ai_response.content)])
        return {
            "agent": "image_creator",
            "response": ai_response.content,
            "session_id": req.session_id,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/pipeline/run")
async def run_pipeline(req: PipelineRequest):
    """
    Full automatic pipeline: message → Strategist → Image Creator → Social Media
    Returns complete result with images and social media content.
    """
    try:
        from core.pipeline import run_pipeline_from_message
        result = await run_pipeline_from_message(
            user_message=req.message,
            client_name=req.client_name,
            num_images=req.num_images,
        )
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/pipeline/brief-to-image")
async def brief_to_image(req: BriefToImageRequest):
    """
    Send an existing brief to Image Creator and Social Media agents.
    Images saved in Supabase Storage: {client_name}/{project_name}/
    """
    try:
        from core.pipeline import run_content_pipeline
        brief = ContentBrief(**req.brief)
        result = await run_content_pipeline(
            brief=brief,
            client_name=req.client_name,
            num_images=req.num_images,
            aspect_ratio=req.aspect_ratio,
            style=req.style,
        )
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/pipeline/stream")
async def pipeline_stream(message: str, client_name: str = "geral", num_images: int = 1):
    """
    SSE stream for pipeline progress:
    strategist_start → strategist_done → image_start → image_done → social_done
    """
    async def generate():
        try:
            yield f"data: {json.dumps({'step': 'strategist_start', 'message': '🔍 Estrategista pesquisando tendências...'})}\n\n"
            await asyncio.sleep(0.1)

            from core.pipeline import run_pipeline_from_message
            task = asyncio.create_task(run_pipeline_from_message(message, client_name, num_images))

            yield f"data: {json.dumps({'step': 'image_start', 'message': '🎨 Gerando imagens com Freepik...'})}\n\n"
            await asyncio.sleep(0.1)

            result = await task

            if result.get("images"):
                for img in result["images"]:
                    idx = img["index"]
                    yield f"data: {json.dumps({'step': 'image_ready', 'message': f'Imagem {idx} gerada', 'url': img['url'], 'folder': img['folder']})}\n\n"

            if result.get("social_media"):
                yield f"data: {json.dumps({'step': 'social_done', 'message': '📱 Conteúdo para Social Media pronto', 'content': result['social_media']['content'][:500]})}\n\n"

            yield f"data: {json.dumps({'step': 'completed', 'result': result})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
