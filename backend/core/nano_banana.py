"""
Freepik Nano Banana (text-to-image) — faster, no polling, base64 response.
This is the model the user has unlimited access to.
"""
import base64
import requests
import structlog
from .config import settings
from .storage import upload_creative, _slugify
import uuid

logger = structlog.get_logger()

FREEPIK_API_BASE = "https://api.freepik.com/v1"

# Valid sizes for Nano Banana
SIZE_MAP = {
    "square_1_1":       "square_1_1",
    "portrait_2_3":     "portrait_2_3",
    "social_story_9_16": "social_story_9_16",
    "widescreen_16_9":  "widescreen_16_9",
    "classic_4_3":      "classic_4_3",
    "traditional_3_4":  "traditional_3_4",
    # Aliases
    "instagram":        "portrait_2_3",
    "stories":          "social_story_9_16",
    "reels":            "social_story_9_16",
    "facebook":         "square_1_1",
    "linkedin":         "widescreen_16_9",
    "feed":             "portrait_2_3",
    "square":           "square_1_1",
}


def generate_nano_banana(
    prompt: str,
    size: str = "square_1_1",
    num_images: int = 1,
) -> dict:
    """Generate image using Freepik Nano Banana (text-to-image).
    Returns base64 image directly — no polling needed. Much faster than Mystic."""
    if not settings.FREEPIK_API_KEY:
        return {"success": False, "error": "FREEPIK_API_KEY não configurada."}

    resolved_size = SIZE_MAP.get(size, "square_1_1")

    try:
        r = requests.post(
            f"{FREEPIK_API_BASE}/ai/text-to-image",
            headers={
                "x-freepik-api-key": settings.FREEPIK_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "prompt": prompt,
                "image": {"size": resolved_size},
                "resolution": "4k",
                "num_images": num_images,
            },
            timeout=60,
        )

        if r.status_code not in (200, 201):
            return {"success": False, "error": f"API error {r.status_code}: {r.text[:200]}"}

        data = r.json()
        images = data.get("data", [])
        if not images:
            return {"success": False, "error": "No images returned"}

        results = []
        for img in images:
            b64 = img.get("base64", "")
            if b64:
                results.append({
                    "base64": b64,
                    "bytes": base64.b64decode(b64),
                })

        return {
            "success": True,
            "images": results,
            "model": "nano-banana",
            "size": resolved_size,
        }

    except Exception as e:
        logger.error("nano_banana_error", error=str(e))
        return {"success": False, "error": str(e)}


def generate_and_store_nano(
    prompt: str,
    size: str = "square_1_1",
    client_name: str = "geral",
    project_name: str = "criativo",
    texts: dict = None,
    logo_url: str = "",
    brand_color: str = "",
    accent_color: str = "",
    layout: str = "bottom_bar",
    compose: bool = True,
) -> dict:
    """Generate with Nano Banana and store in Supabase Storage. Synchronous."""
    result = generate_nano_banana(prompt, size)
    if not result.get("success"):
        return result

    images = result.get("images", [])
    if not images:
        return {"success": False, "error": "No images to store"}

    img_bytes = images[0]["bytes"]

    # ── Compose ad if requested ──
    if compose and texts:
        try:
            from .image_compositor import compose_ad
            composed = compose_ad(
                base_image_bytes=img_bytes,
                texts=texts,
                logo_url=logo_url,
                brand_color=brand_color or "#1a1a1a",
                accent_color=accent_color or "#fccc04",
                layout=layout,
            )
            img_bytes = composed
        except Exception as e:
            logger.warning("composition_failed", error=str(e))

    client_slug = _slugify(client_name)
    project_slug = _slugify(project_name)
    fname = f"{uuid.uuid4().hex[:8]}.jpg"
    path = f"{client_slug}/{project_slug}/{fname}"

    try:
        from .config import settings as cfg
        SUPABASE_STORAGE_URL = f"{cfg.SUPABASE_URL}/storage/v1"
        HEADERS = {"Authorization": f"Bearer {cfg.SUPABASE_KEY}", "apikey": cfg.SUPABASE_KEY}

        up = requests.post(
            f"{SUPABASE_STORAGE_URL}/object/creatives/{path}",
            headers={**HEADERS, "Content-Type": "image/jpeg"},
            data=img_bytes, timeout=30,
        )
        pub_url = f"{cfg.SUPABASE_URL}/storage/v1/object/public/creatives/{path}"
        return {
            "success": True,
            "image_url": pub_url,
            "folder": f"{client_slug}/{project_slug}/",
            "path": path,
            "model": "nano-banana",
            "provider": "freepik",
            "composed": compose and bool(texts),
        }
    except Exception as e:
        b64_str = base64.b64encode(img_bytes).decode()
        return {
            "success": True,
            "image_url": f"data:image/jpeg;base64,{b64_str}",
            "model": "nano-banana",
            "provider": "freepik",
            "storage_error": str(e),
        }
