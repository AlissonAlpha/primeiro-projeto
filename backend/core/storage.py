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


async def upload_creative(file_bytes: bytes, filename: str, content_type: str) -> dict:
    await ensure_bucket()
    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    path = f"ads/{unique_name}"

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
        "public_url": public_url,
        "filename": unique_name,
        "original_name": filename,
        "content_type": content_type,
    }


async def delete_creative(path: str):
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"{SUPABASE_STORAGE_URL}/object/{BUCKET}/{path}",
            headers=HEADERS,
        )
