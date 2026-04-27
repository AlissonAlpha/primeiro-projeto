from langchain_core.tools import tool
from typing import Optional
import requests
import structlog
from datetime import datetime
from core.config import settings

logger = structlog.get_logger()


@tool
def save_brand_from_logo_url(
    client_name: str,
    logo_url: str,
    ad_account_id: str = "",
) -> dict:
    """Extract brand colors from a logo URL and save to brand settings.
    Use this when the user shares a logo image URL (from 📎 upload).
    The colors will be automatically used in all future image generations for this client."""
    try:
        import requests as req
        from core.brand_identity import extract_colors_from_bytes, save_brand_settings, store_brand_logo
        from core.config import settings as cfg

        # Download the logo
        r = req.get(logo_url, timeout=15)
        if r.status_code != 200:
            return {"success": False, "error": f"Não consegui baixar a logo: {r.status_code}"}

        img_bytes = r.content

        # Store logo in Supabase
        logo_result = store_brand_logo(img_bytes, client_name, "logo.jpg")

        # Extract colors
        colors = extract_colors_from_bytes(img_bytes)
        if not colors.get("success"):
            return {"success": False, "error": colors.get("error")}

        # Save to account_settings
        if ad_account_id:
            save_brand_settings(ad_account_id, client_name, logo_result.get("logo_url", logo_url), colors)
        else:
            # Save by client name only
            import requests as rq
            SUPABASE_URL = cfg.SUPABASE_URL
            HEADERS = {
                "Authorization": f"Bearer {cfg.SUPABASE_KEY}",
                "apikey": cfg.SUPABASE_KEY,
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=representation",
            }
            rq.post(f"{SUPABASE_URL}/rest/v1/account_settings", headers=HEADERS, json={
                "ad_account_id": f"brand_{client_name.lower().replace(' ', '_')}",
                "account_name": client_name,
                "logo_url": logo_result.get("logo_url", logo_url),
                "brand_colors": colors.get("prompt_colors", ""),
                "brand_palette": str(colors.get("palette", [])),
            })

        return {
            "success": True,
            "client": client_name,
            "dominant_color": colors.get("dominant"),
            "palette": colors.get("palette", []),
            "prompt_colors": colors.get("prompt_colors", ""),
            "message": f"Cores da marca {client_name} extraídas e salvas! Serão usadas em todas as próximas artes.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


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
    client_name: str = "geral",
    references: list[str] = [],
    generate_image: bool = True,
) -> dict:
    """Generate a complete Content Brief AND automatically trigger image generation.
    Always set generate_image=True so the image is created immediately after the brief.
    client_name: use the actual client/brand name for folder organization (e.g. 'Gotrix')."""
    logger.info("generating_content_brief", segment=segment, theme=theme, client=client_name)

    # Build optimized image prompt
    # Freepik Mystic valid aspect ratios
    aspect_map = {
        "instagram": "portrait_2_3",      # Feed Instagram (similar to 4:5)
        "stories": "social_story_9_16",   # Stories/Reels
        "reels": "social_story_9_16",     # Reels
        "facebook": "square_1_1",         # Facebook feed
        "linkedin": "widescreen_16_9",    # LinkedIn
        "feed": "portrait_2_3",           # Generic feed
        "story": "social_story_9_16",
        "carrossel": "square_1_1",
    }
    aspect_ratio = aspect_map.get(format.lower(), aspect_map.get(platform.lower(), "square_1_1"))

    image_prompt = (
        f"{visual_direction}. "
        f"Professional commercial marketing photography for {segment} in Brazil. "
        f"Theme: {theme}. Emotion conveyed: {emotion}. "
        f"Ultra high quality 4K, sharp focus, perfect composition, "
        f"professional studio or natural lighting, vibrant and engaging, "
        f"suitable for {platform} {format} advertising. "
        f"No text overlays, no watermarks, no logos."
    )

    from core.content_brief import ContentBrief
    brief = ContentBrief(
        segment=segment, theme=theme, hook=hook, emotion=emotion,
        format=format, platform=platform, copy_direction=copy_direction,
        visual_direction=visual_direction, image_prompt=image_prompt,
        cta=cta, references=references, status="brief_ready",
    )

    result = {
        "success": True,
        "brief_id": brief.id,
        "brief": brief.model_dump(),
        "image_status": "pending",
        "image_url": None,
        "folder": None,
    }

    # Auto-trigger image generation using Nano Banana
    if generate_image:
        try:
            from core.nano_banana import generate_and_store_nano
            from core.brand_identity import get_brand_colors_prompt

            # Enrich prompt with brand colors if available
            brand_colors = get_brand_colors_prompt(client_name)
            final_prompt = f"{image_prompt}. {brand_colors}" if brand_colors else image_prompt

            # Get logo and colors for composition
            from core.brand_identity import get_brand_logo_url
            logo = get_brand_logo_url(client_name)
            # Parse dominant color from brand_colors string
            dom_color = ""
            acc_color = ""
            if brand_colors:
                import re
                hexes = re.findall(r'#[0-9a-fA-F]{6}', brand_colors)
                if hexes:
                    dom_color = hexes[0]
                    acc_color = hexes[1] if len(hexes) > 1 else hexes[0]

            img = generate_and_store_nano(
                prompt=final_prompt,
                size=aspect_ratio,
                client_name=client_name,
                project_name=theme,
                headline=hook[:50] if hook else theme[:50],
                subtext=copy_direction[:60] if copy_direction else "",
                cta_text=cta[:20] if cta else "Saiba Mais",
                logo_url=logo,
                brand_color=dom_color or "#1A1A2E",
                accent_color=acc_color or "#E8A020",
                layout="bottom_bar",
                compose=True,
            )
            if img.get("success") and img.get("image_url"):
                from core.storage import _slugify
                result["image_url"] = img["image_url"]
                result["folder"] = img.get("folder", f"{_slugify(client_name)}/{_slugify(theme)}/")
                result["image_status"] = "generated"
                result["model"] = "nano-banana"
                brief.generated_image_url = img["image_url"]
                brief.status = "image_generated"
            else:
                result["image_status"] = "failed"
                result["image_error"] = img.get("error", "Unknown error")
        except Exception as e:
            result["image_status"] = "failed"
            result["image_error"] = str(e)

    return result


STRATEGIST_TOOLS = [
    save_brand_from_logo_url,
    search_trends,
    analyze_competitors,
    get_commemorative_dates,
    generate_content_brief,
]
