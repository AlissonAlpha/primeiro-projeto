from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from core.storage import upload_creative
from core.meta_ads_builder import create_ad_set, create_ad_creative, create_ad, build_targeting

router = APIRouter(prefix="/creatives", tags=["creatives"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime"}
MAX_SIZE_MB = 30


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a creative image or video to Supabase Storage."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Tipo não suportado: {file.content_type}. Use: JPG, PNG, WEBP, MP4.")

    data = await file.read()
    size_mb = len(data) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(400, f"Arquivo muito grande: {size_mb:.1f}MB. Máximo: {MAX_SIZE_MB}MB.")

    try:
        result = await upload_creative(data, file.filename or "creative", file.content_type)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(500, str(e))


class CreateAdRequest(BaseModel):
    ad_account_id: str
    campaign_id: str
    ad_set_name: str
    ad_name: str
    page_id: str
    image_url: str
    primary_text: str
    headline: str
    description: str
    cta_button: str
    link_url: str
    daily_budget_brl: float = 30.0
    age_min: int = 18
    age_max: int = 65
    countries: list[str] = ["BR"]
    campaign_objective: str = "OUTCOME_LEADS"


@router.post("/create-full-ad")
async def create_full_ad(req: CreateAdRequest):
    """Create a complete ad: Ad Set + Creative + Ad linked to an existing campaign."""
    try:
        # 1. Ad Set
        targeting = build_targeting(
            age_min=req.age_min,
            age_max=req.age_max,
            geo_locations={"countries": req.countries},
        )
        ad_set = create_ad_set(
            ad_account_id=req.ad_account_id,
            campaign_id=req.campaign_id,
            name=req.ad_set_name,
            daily_budget_cents=int(req.daily_budget_brl * 100),
            targeting=targeting,
            campaign_objective=req.campaign_objective,
            status="PAUSED",
        )

        # 2. Creative (usando URL da imagem já upada no Supabase)
        creative = create_ad_creative(
            ad_account_id=req.ad_account_id,
            name=f"{req.ad_name} - Creative",
            page_id=req.page_id,
            image_hash="",  # será substituído por upload direto ao Meta
            primary_text=req.primary_text,
            headline=req.headline,
            description=req.description,
            cta_type=req.cta_button,
            link_url=req.link_url,
        )

        # 3. Ad
        ad = create_ad(
            ad_account_id=req.ad_account_id,
            name=req.ad_name,
            ad_set_id=ad_set["id"],
            creative_id=creative["id"],
            status="PAUSED",
        )

        return {
            "success": True,
            "ad_set": ad_set,
            "creative": creative,
            "ad": ad,
            "message": "Anúncio completo criado e pausado para revisão.",
        }
    except Exception as e:
        raise HTTPException(500, str(e))
