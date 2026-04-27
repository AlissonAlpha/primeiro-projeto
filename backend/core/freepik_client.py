import requests
import httpx
import asyncio
import structlog
from .config import settings
from .storage import upload_creative

logger = structlog.get_logger()

FREEPIK_API_BASE = "https://api.freepik.com/v1"


def generate_image_sync(
    prompt: str,
    aspect_ratio: str = "square_1_1",
    style_preset: str = "photo",
    negative_prompt: str = "text, watermark, logo, blurry, low quality",
) -> dict:
    """Generate image using Freepik Mystic API (synchronous)."""
    if not settings.FREEPIK_API_KEY:
        return {
            "success": False,
            "error": "FREEPIK_API_KEY não configurada.",
            "mock": True,
        }

    headers = {
        "x-freepik-api-key": settings.FREEPIK_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Submit generation job
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "guidance_scale": 7,
        "aspect_ratio": aspect_ratio,  # square_1_1 | portrait_3_4 | portrait_9_16 | landscape_4_3 | landscape_16_9
        "num_images": 1,
        "styling": {
            "style": style_preset,  # photo | digital-art | illustration | 3d | painting
        },
    }

    try:
        r = requests.post(f"{FREEPIK_API_BASE}/ai/mystic", headers=headers, json=payload, timeout=60)
        data = r.json()

        if r.status_code not in (200, 201):
            return {"success": False, "error": data.get("message", str(data))}

        # Handle async generation (poll if needed)
        task_id = data.get("data", {}).get("task_id") or data.get("task_id")
        if task_id:
            return _poll_freepik_task(task_id, headers)

        # Direct response (non-async)
        generated = data.get("data", {}).get("generated") or data.get("generated", [])
        if generated:
            url = generated[0] if isinstance(generated[0], str) else generated[0].get("url") or generated[0].get("src")
            return {"success": True, "image_url": url, "provider": "freepik"}

        return {"success": False, "error": "Nenhuma imagem retornada", "raw": data}

    except Exception as e:
        logger.error("freepik_error", error=str(e))
        return {"success": False, "error": str(e)}


def _poll_freepik_task(task_id: str, headers: dict, max_attempts: int = 30) -> dict:
    """Poll Freepik for async task completion."""
    import time
    for _ in range(max_attempts):
        time.sleep(3)
        r = requests.get(f"{FREEPIK_API_BASE}/ai/mystic/{task_id}", headers=headers, timeout=15)
        data = r.json()
        status = data.get("data", {}).get("status") or data.get("status", "")

        if status in ("completed", "succeeded", "done", "COMPLETED", "SUCCEEDED"):
            generated = data.get("data", {}).get("generated") or data.get("generated", [])
            if generated:
                # Freepik returns list of URL strings
                url = generated[0] if isinstance(generated[0], str) else generated[0].get("url") or generated[0].get("src")
                return {"success": True, "image_url": url, "provider": "freepik", "task_id": task_id}

        if status in ("failed", "error", "FAILED", "ERROR"):
            return {"success": False, "error": f"Freepik task failed: {status}", "raw": data}

    return {"success": False, "error": "Timeout aguardando geração da imagem Freepik."}


async def generate_and_store(prompt: str, aspect_ratio: str = "square_1_1", style: str = "photo") -> dict:
    """Generate image with Freepik and store in Supabase Storage."""
    result = generate_image_sync(prompt, aspect_ratio, style)
    if not result.get("success"):
        return result

    image_url = result["image_url"]

    # Download and store in Supabase for persistence
    try:
        async with httpx.AsyncClient() as client:
            img_r = await client.get(image_url, timeout=30)
            img_bytes = img_r.content

        ext = "jpg"
        stored = await upload_creative(img_bytes, f"generated.{ext}", "image/jpeg")
        return {
            "success": True,
            "freepik_url": image_url,
            "stored_url": stored["public_url"],
            "provider": "freepik",
        }
    except Exception as e:
        # Return original URL if storage fails
        return {"success": True, "freepik_url": image_url, "stored_url": image_url, "provider": "freepik"}
