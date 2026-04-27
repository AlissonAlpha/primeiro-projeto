import httpx
import uuid
from pathlib import Path
from .config import settings

BUCKET = "creatives"
SUPABASE_STORAGE_URL = f"{settings.SUPABASE_URL}/storage/v1"
HEADERS = {
    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    "apikey": settings.SUPABASE_KEY,
}


async def ensure_bucket():
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{SUPABASE_STORAGE_URL}/bucket",
            headers=HEADERS,
            json={"id": BUCKET, "name": BUCKET, "public": True},
        )
        # 409 = already exists, both are fine
        return r.status_code in (200, 201, 409)


def _slugify(text: str) -> str:
    import re, unicodedata

    # Remove suffixes that create duplicate folders
    _noise = r"\b(test|teste|final|compositor|debug|4k|2k|hd|pro|v\d+|\d+)\b"
    text = re.sub(_noise, "", text, flags=re.IGNORECASE)

    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", text).strip("-")

    # Limit to first 3 words to keep folder names clean
    parts = slug.split("-")
    slug = "-".join(p for p in parts[:4] if p)

    return slug[:35]


async def upload_creative(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    client_name: str = "geral",
    project_name: str = "ads",
) -> dict:
    await ensure_bucket()
    ext = Path(filename).suffix or ".jpg"
    unique_name = f"{uuid.uuid4().hex[:8]}{ext}"
    client_slug = _slugify(client_name)
    project_slug = _slugify(project_name)
    path = f"{client_slug}/{project_slug}/{unique_name}"

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{SUPABASE_STORAGE_URL}/object/{BUCKET}/{path}",
            headers={**HEADERS, "Content-Type": content_type},
            content=file_bytes,
        )
        if r.status_code not in (200, 201):
            raise Exception(f"Upload failed: {r.text}")

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{path}"
    return {
        "path": path,
        "folder": f"{client_slug}/{project_slug}/",
        "public_url": public_url,
        "filename": unique_name,
        "original_name": filename,
        "content_type": content_type,
        "client": client_name,
        "project": project_name,
    }


async def delete_creative(path: str):
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"{SUPABASE_STORAGE_URL}/object/{BUCKET}/{path}",
            headers=HEADERS,
        )
