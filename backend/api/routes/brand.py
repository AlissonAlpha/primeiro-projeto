from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from core.brand_identity import (
    extract_colors_from_bytes,
    store_brand_logo,
    save_brand_settings,
    get_brand_colors_prompt,
)
from core.account_settings import get_account_settings_sync

router = APIRouter(prefix="/brand", tags=["brand"])


@router.post("/upload-logo")
async def upload_logo(
    file: UploadFile = File(...),
    client_name: str = Form(...),
    ad_account_id: str = Form(""),
):
    """Upload brand logo, extract colors, and save brand identity."""
    allowed = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
    if file.content_type not in allowed:
        raise HTTPException(400, f"Formato não suportado: {file.content_type}")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(400, "Arquivo muito grande. Máximo: 10MB.")

    # Store logo
    logo_result = store_brand_logo(data, client_name, file.filename or "logo.png")
    if not logo_result.get("success"):
        raise HTTPException(500, logo_result.get("error", "Erro no upload"))

    # Extract colors (skip for SVG)
    colors = {"success": True, "dominant": "", "palette": [], "prompt_colors": ""}
    if file.content_type != "image/svg+xml":
        colors = extract_colors_from_bytes(data)

    # Save to account_settings if account provided
    if ad_account_id:
        save_brand_settings(ad_account_id, client_name, logo_result["logo_url"], colors)

    return {
        "success": True,
        "client": client_name,
        "logo_url": logo_result["logo_url"],
        "colors": {
            "dominant": colors.get("dominant"),
            "palette": colors.get("palette", []),
            "prompt_colors": colors.get("prompt_colors", ""),
            "dark_colors": colors.get("dark_colors", []),
            "light_colors": colors.get("light_colors", []),
        },
    }


@router.get("/identity/{ad_account_id}")
async def get_brand_identity(ad_account_id: str):
    """Get saved brand identity for an account."""
    try:
        cfg = get_account_settings_sync(ad_account_id)
        if not cfg:
            return {"found": False}
        import json
        palette = []
        try:
            palette = json.loads(cfg.get("brand_palette") or "[]")
        except Exception:
            pass
        return {
            "found": True,
            "account_name": cfg.get("account_name"),
            "logo_url": cfg.get("logo_url"),
            "brand_colors": cfg.get("brand_colors"),
            "palette": palette,
        }
    except Exception as e:
        raise HTTPException(500, str(e))
