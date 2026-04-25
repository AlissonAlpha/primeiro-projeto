from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage

from backend.agents.traffic_manager.agent import traffic_manager_agent
from backend.agents.social_media.agent import social_media_agent
from backend.agents.ceo.agent import ceo_agent

router = APIRouter(prefix="/agents", tags=["agents"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    agent: str
    response: str
    session_id: Optional[str] = None


@router.post("/traffic-manager/chat", response_model=ChatResponse)
async def chat_traffic_manager(request: ChatRequest):
    try:
        result = traffic_manager_agent.invoke({
            "messages": [HumanMessage(content=request.message)],
            "current_step": "start",
        })
        last_message = result["messages"][-1]
        return ChatResponse(
            agent="traffic_manager",
            response=last_message.content,
            session_id=request.session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social-media/chat", response_model=ChatResponse)
async def chat_social_media(request: ChatRequest):
    try:
        result = social_media_agent.invoke({
            "messages": [HumanMessage(content=request.message)],
            "current_step": "start",
        })
        last_message = result["messages"][-1]
        return ChatResponse(
            agent="social_media",
            response=last_message.content,
            session_id=request.session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ceo/chat", response_model=ChatResponse)
async def chat_ceo(request: ChatRequest):
    try:
        result = ceo_agent.invoke({
            "messages": [HumanMessage(content=request.message)],
            "current_step": "start",
        })
        last_message = result["messages"][-1]
        return ChatResponse(
            agent="ceo",
            response=last_message.content,
            session_id=request.session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
