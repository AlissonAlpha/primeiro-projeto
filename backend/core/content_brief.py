from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid


class ContentBrief(BaseModel):
    """Structured brief passed from Strategist → Image Creator → Social Media."""
    id: str = ""
    client_id: Optional[str] = None
    segment: str                    # Ex: "concessionária de motos"
    theme: str                      # Ex: "Sábado de Ofertas — Dia das Mães"
    hook: str                       # Ex: "Sua mãe merece uma moto nova"
    emotion: str                    # Ex: "alegria, surpresa, urgência"
    format: str                     # Ex: "post feed", "story", "reels", "carrossel"
    platform: str                   # Ex: "instagram", "facebook", "linkedin"
    copy_direction: str             # Ex: "Copy curta, CTA direto no WhatsApp"
    visual_direction: str           # Ex: "Foto de mãe e filha felizes com moto, cores quentes"
    image_prompt: str               # Prompt otimizado para geração de imagem
    caption: str = ""               # Caption gerada para o post
    hashtags: list[str] = []
    cta: str = ""                   # Ex: "Clique no link da bio"
    best_time: str = ""             # Ex: "Sábado 10h"
    references: list[str] = []      # URLs de referência/tendências encontradas
    generated_image_url: str = ""   # Preenchido pelo Image Creator
    status: str = "brief_ready"     # brief_ready → image_generated → post_scheduled → published
    created_at: str = ""

    def __init__(self, **data):
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())
        if not data.get("created_at"):
            data["created_at"] = datetime.now().isoformat()
        super().__init__(**data)
