from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agents.traffic_manager.agent import traffic_manager_agent
from agents.social_media.agent import social_media_agent
from agents.ceo.agent import ceo_agent
from core.session import get_session, save_session, clear_session, append_messages

router = APIRouter(prefix="/agents", tags=["agents"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    agent: str
    response: str
    session_id: Optional[str] = None


def _chat(agent, agent_name: str, message: str, session_id: Optional[str]) -> ChatResponse:
    history = get_session(session_id) if session_id else []
    user_msg = HumanMessage(content=message)
    all_messages = history + [user_msg]

    result = agent.invoke({
        "messages": all_messages,
        "current_step": "start",
    })

    ai_response = result["messages"][-1]

    if session_id:
        # Only save HumanMessage + final AIMessage (no tool_calls or ToolMessages).
        # Saving intermediate tool_calls causes re-execution on the next turn.
        final_ai = AIMessage(content=ai_response.content)
        append_messages(session_id, [user_msg, final_ai])

    return ChatResponse(
        agent=agent_name,
        response=ai_response.content,
        session_id=session_id,
    )


@router.post("/traffic-manager/chat", response_model=ChatResponse)
async def chat_traffic_manager(request: ChatRequest):
    try:
        return _chat(traffic_manager_agent, "traffic_manager", request.message, request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social-media/chat", response_model=ChatResponse)
async def chat_social_media(request: ChatRequest):
    try:
        return _chat(social_media_agent, "social_media", request.message, request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ceo/chat", response_model=ChatResponse)
async def chat_ceo(request: ChatRequest):
    try:
        return _chat(ceo_agent, "ceo", request.message, request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    clear_session(session_id)
    return {"success": True}
