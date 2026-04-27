from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage
from agents.content_strategist.agent import content_strategist_agent
from agents.image_creator.agent import image_creator_agent
from core.session import get_session, append_messages
from langchain_core.messages import AIMessage

router = APIRouter(prefix="/content", tags=["content"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class GenerateImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "square_1_1"
    style: str = "photo"
    brief_id: Optional[str] = None


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

        # Extract brief if generated
        brief = result.get("brief")
        return {
            "agent": "content_strategist",
            "response": ai_response.content,
            "brief": brief,
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


@router.post("/generate-image")
async def generate_image(req: GenerateImageRequest):
    try:
        from core.freepik_client import generate_image_sync
        result = generate_image_sync(req.prompt, req.aspect_ratio, req.style)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/full-pipeline")
async def run_full_pipeline(req: ChatRequest):
    """Run the full pipeline: Strategist → Image Creator → return brief + image."""
    try:
        # Step 1: Strategist generates brief
        strat_result = content_strategist_agent.invoke({
            "messages": [HumanMessage(content=req.message)],
            "current_step": "start",
        })
        strat_response = strat_result["messages"][-1].content

        # Step 2: Send brief to Image Creator
        img_result = image_creator_agent.invoke({
            "messages": [HumanMessage(content=f"Gere uma imagem para este brief:\n\n{strat_response}")],
            "current_step": "start",
        })
        img_response = img_result["messages"][-1].content

        return {
            "strategist_output": strat_response,
            "image_creator_output": img_response,
            "pipeline": "strategist → image_creator",
        }
    except Exception as e:
        raise HTTPException(500, str(e))
