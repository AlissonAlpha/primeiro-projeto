from langchain_core.tools import tool
from typing import Optional
import requests
import structlog
from datetime import datetime
from core.config import settings

logger = structlog.get_logger()


@tool
def search_trends(query: str, segment: str = "") -> dict:
    """Search for current trends, news and viral content in a segment.
    Use this to find hooks, opportunities and relevant topics for content creation."""
    try:
        if settings.TAVILY_API_KEY:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": settings.TAVILY_API_KEY,
                "query": f"{query} {segment} tendências viral 2026",
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
            }, timeout=15)
            data = r.json()
            return {
                "success": True,
                "answer": data.get("answer", ""),
                "results": [{"title": r["title"], "url": r["url"], "content": r["content"][:300]}
                            for r in data.get("results", [])],
            }
        else:
            return {
                "success": False,
                "message": "TAVILY_API_KEY não configurada. Configure em .env para pesquisa real.",
                "mock_trends": [
                    f"Tendência 1: Conteúdo com antes/depois para {segment}",
                    f"Tendência 2: Vídeos curtos mostrando bastidores de {segment}",
                    f"Tendência 3: Depoimentos reais de clientes em {segment}",
                ]
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def analyze_competitors(segment: str, location: str = "Brasil") -> dict:
    """Analyze what competitors are posting to identify content gaps and opportunities."""
    try:
        if settings.TAVILY_API_KEY:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": settings.TAVILY_API_KEY,
                "query": f"melhores posts instagram {segment} {location} 2026 engajamento viral",
                "search_depth": "basic",
                "max_results": 5,
            }, timeout=15)
            data = r.json()
            return {
                "success": True,
                "insights": [{"title": r["title"], "content": r["content"][:300]}
                             for r in data.get("results", [])],
            }
        else:
            return {
                "success": False,
                "message": "TAVILY_API_KEY não configurada.",
                "mock_insights": [f"Concorrentes de {segment} estão usando muito vídeo curto e promoções relâmpago."]
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_commemorative_dates(month: Optional[str] = None) -> dict:
    """Get upcoming commemorative dates and events relevant for content planning."""
    dates = {
        "janeiro": ["1 — Ano Novo", "2ª sem — Volta às aulas", "25 — Dia do Turismo"],
        "fevereiro": ["Carnaval (data variável)", "14 — Dia dos Namorados (alguns países)"],
        "março": ["8 — Dia da Mulher", "20 — Início do Outono", "22 — Dia da Água"],
        "abril": ["Páscoa (data variável)", "1 — Dia da Mentira", "22 — Dia do Planeta Terra"],
        "maio": ["1 — Dia do Trabalho", "2ª dom — Dia das Mães", "31 — Dia sem Tabaco"],
        "junho": ["Festas Juninas", "12 — Dia dos Namorados", "29 — Dia de São Pedro"],
        "julho": ["Férias escolares", "Dia do Amigo (20)"],
        "agosto": ["11 — Dia do Estudante", "22 — Dia do Folclore"],
        "setembro": ["7 — Dia da Independência", "15 — Dia do Cliente", "21 — Primavera"],
        "outubro": ["1 — Dia das Crianças", "12 — Nossa Senhora Aparecida", "31 — Halloween"],
        "novembro": ["2 — Finados", "15 — Proclamação da República", "Black Friday"],
        "dezembro": ["Natal (25)", "Ano Novo (31)", "Cyber Monday"],
    }
    target = month or datetime.now().strftime("%B").lower()
    return {
        "success": True,
        "month": target,
        "dates": dates.get(target, dates.get(datetime.now().strftime("%B").lower(), [])),
        "tip": "Use datas comemorativas para criar ganchos relevantes e urgência natural.",
    }


@tool
def generate_content_brief(
    segment: str,
    theme: str,
    platform: str,
    format: str,
    emotion: str,
    hook: str,
    visual_direction: str,
    copy_direction: str,
    cta: str,
    references: list[str] = [],
) -> dict:
    """Generate a complete structured Content Brief to be sent to the Image Creator and Social Media agents.
    This is the final output of the strategist — a complete creative brief."""
    logger.info("generating_content_brief", segment=segment, theme=theme)

    # Build optimized image generation prompt
    image_prompt = (
        f"Professional marketing photo for {segment}. "
        f"Theme: {theme}. "
        f"Visual: {visual_direction}. "
        f"Style: photorealistic, high quality, vibrant colors, "
        f"suitable for social media {platform} advertising. "
        f"Emotion: {emotion}. No text overlays."
    )

    from core.content_brief import ContentBrief
    brief = ContentBrief(
        segment=segment,
        theme=theme,
        hook=hook,
        emotion=emotion,
        format=format,
        platform=platform,
        copy_direction=copy_direction,
        visual_direction=visual_direction,
        image_prompt=image_prompt,
        cta=cta,
        references=references,
        status="brief_ready",
    )

    return {
        "success": True,
        "brief": brief.model_dump(),
        "next_step": "Enviar para o Criador de Imagens para gerar o visual.",
    }


STRATEGIST_TOOLS = [
    search_trends,
    analyze_competitors,
    get_commemorative_dates,
    generate_content_brief,
]
