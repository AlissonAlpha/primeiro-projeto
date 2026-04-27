"""Brand identity: logo upload, color extraction, brand guidelines storage."""
import io
import requests as req_lib
import structlog
from PIL import Image
from colorthief import ColorThief
from .config import settings
from .storage import _slugify, upload_creative
import asyncio

logger = structlog.get_logger()

SUPABASE_URL = settings.SUPABASE_URL
HEADERS = {
    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    "apikey": settings.SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=representation",
}


def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def extract_colors_from_bytes(image_bytes: bytes, num_colors: int = 5) -> dict:
    """Extract dominant colors from image bytes using ColorThief."""
    try:
        img_file = io.BytesIO(image_bytes)
        ct = ColorThief(img_file)
        dominant = ct.get_color(quality=1)
        palette = ct.get_palette(color_count=num_colors, quality=1)

        hex_dominant = rgb_to_hex(dominant)
        hex_palette = [rgb_to_hex(c) for c in palette]

        # Classify colors
        def luminance(rgb):
            r, g, b = [x / 255.0 for x in rgb]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        sorted_palette = sorted(palette, key=luminance)
        dark_colors = [rgb_to_hex(c) for c in sorted_palette[:2]]
        light_colors = [rgb_to_hex(c) for c in sorted_palette[-2:]]

        return {
            "success": True,
            "dominant": hex_dominant,
            "palette": hex_palette,
            "dark_colors": dark_colors,
            "light_colors": light_colors,
            "prompt_colors": f"Use brand colors: primary {hex_dominant}, palette {', '.join(hex_palette[:3])}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def store_brand_logo(image_bytes: bytes, client_name: str, filename: str = "logo.png") -> dict:
    """Upload brand logo to Supabase Storage under brands/{client}/logo.ext"""
    try:
        client_slug = _slugify(client_name)
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "png"
        path = f"brands/{client_slug}/logo.{ext}"
        content_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"

        up = req_lib.post(
            f"{SUPABASE_URL}/storage/v1/object/creatives/{path}",
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                "apikey": settings.SUPABASE_KEY,
                "Content-Type": content_type,
                "x-upsert": "true",
            },
            content=image_bytes, timeout=30,
        )
        pub_url = f"{SUPABASE_URL}/storage/v1/object/public/creatives/{path}"
        return {"success": True, "logo_url": pub_url, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_brand_settings(
    ad_account_id: str,
    client_name: str,
    logo_url: str,
    colors: dict,
    brand_voice: str = "",
    fonts: str = "",
) -> dict:
    """Save brand identity to account_settings in Supabase."""
    try:
        import json
        brand_data = {
            "logo_url": logo_url,
            "dominant_color": colors.get("dominant", ""),
            "palette": json.dumps(colors.get("palette", [])),
            "prompt_colors": colors.get("prompt_colors", ""),
            "brand_voice": brand_voice,
            "fonts": fonts,
        }
        payload = {
            "ad_account_id": ad_account_id,
            "account_name": client_name,
            "logo_url": logo_url,
            "brand_colors": colors.get("prompt_colors", ""),
            "brand_palette": json.dumps(colors.get("palette", [])),
        }
        r = req_lib.post(
            f"{SUPABASE_URL}/rest/v1/account_settings",
            headers=HEADERS, json=payload,
        )
        return {"success": True, "brand": brand_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_brand_colors_prompt(client_name_or_account_id: str) -> str:
    """Get saved brand color prompt by client name or ad_account_id."""
    try:
        h = {"Authorization": f"Bearer {settings.SUPABASE_KEY}", "apikey": settings.SUPABASE_KEY}
        # Try by account_id first
        r = req_lib.get(f"{SUPABASE_URL}/rest/v1/account_settings", headers=h,
            params={"ad_account_id": f"eq.{client_name_or_account_id}", "limit": "1"})
        data = r.json()
        if data:
            return data[0].get("brand_colors", "")
        # Fallback: search by account_name (case-insensitive)
        r2 = req_lib.get(f"{SUPABASE_URL}/rest/v1/account_settings", headers=h,
            params={"account_name": f"ilike.{client_name_or_account_id}", "limit": "1"})
        data2 = r2.json()
        if data2:
            return data2[0].get("brand_colors", "")
        return ""
    except Exception:
        return ""


def get_brand_logo_url(client_name: str) -> str:
    """Get saved logo URL by client name."""
    try:
        h = {"Authorization": f"Bearer {settings.SUPABASE_KEY}", "apikey": settings.SUPABASE_KEY}
        r = req_lib.get(f"{SUPABASE_URL}/rest/v1/account_settings", headers=h,
            params={"account_name": f"ilike.{client_name}", "limit": "1"})
        data = r.json()
        if data:
            return data[0].get("logo_url", "")
        return ""
    except Exception:
        return ""
