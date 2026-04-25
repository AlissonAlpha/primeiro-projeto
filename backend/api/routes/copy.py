from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from langchain_core.messages import HumanMessage
from agents.copy_agent.agent import copy_agent

router = APIRouter(prefix="/copy", tags=["copy-agent"])


class CopyBriefRequest(BaseModel):
    product: str
    audience: str
    objective: str
    tone: str = "profissional"
    differentials: str = ""
    cta_hint: str = ""


class CopyVariation(BaseModel):
    hook: str
    headline: str
    primary_text: str
    description: str
    cta_button: str


class GenerateCopyResponse(BaseModel):
    variations: List[CopyVariation]
    raw_response: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/generate")
async def generate_copy(req: CopyBriefRequest):
    """Generate 3 ad copy variations from a brief."""
    try:
        prompt = f"""Crie 3 variações de copy para anúncio no Meta Ads com o seguinte briefing:

**Produto/Serviço:** {req.product}
**Público-alvo:** {req.audience}
**Objetivo da campanha:** {req.objective}
**Tom de voz:** {req.tone}
**Diferenciais:** {req.differentials or "Não informado"}
**CTA desejado:** {req.cta_hint or "Sugerir o mais adequado"}

Gere as 3 variações com hook, headline, primary text, description e CTA button.
Formate cada variação claramente e também inclua um bloco ```json``` com as 3 variações estruturadas."""

        result = copy_agent.invoke({
            "messages": [HumanMessage(content=prompt)],
            "current_step": "start",
        })

        response_text = result["messages"][-1].content
        return {"raw_response": response_text, "brief": req.model_dump()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_copy_agent(req: ChatRequest):
    """Chat with the copy agent for ad copy creation and refinement."""
    try:
        result = copy_agent.invoke({
            "messages": [HumanMessage(content=req.message)],
            "current_step": "start",
        })
        return {
            "agent": "copy",
            "response": result["messages"][-1].content,
            "session_id": req.session_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
