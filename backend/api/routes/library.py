from fastapi import APIRouter, HTTPException
import requests
from core.config import settings

router = APIRouter(prefix="/library", tags=["library"])

SUPABASE_URL = settings.SUPABASE_URL
BUCKET = "creatives"
HEADERS = {
    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    "apikey": settings.SUPABASE_KEY,
    "Content-Type": "application/json",
}


def list_prefix(prefix: str = "") -> list:
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET}",
        headers=HEADERS,
        json={"prefix": prefix, "limit": 200, "offset": 0},
    )
    return r.json() if r.status_code == 200 else []


@router.get("/folders")
async def get_folders():
    """List all client folders in the creatives bucket."""
    try:
        items = list_prefix("")
        folders = []
        for item in items:
            if isinstance(item, dict) and item.get("id") is None:
                # It's a folder (no id means it's a prefix)
                name = item.get("name", "")
                if name:
                    # Count files inside
                    sub = list_prefix(f"{name}/")
                    file_count = sum(1 for i in sub if isinstance(i, dict) and i.get("id"))
                    sub_folders = [i.get("name") for i in sub if isinstance(i, dict) and not i.get("id") and i.get("name")]
                    folders.append({
                        "name": name,
                        "file_count": file_count,
                        "sub_folders": sub_folders,
                    })
        return {"folders": folders, "total": len(folders)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/files")
async def get_files(prefix: str = ""):
    """List files in a specific folder path."""
    try:
        path = f"{prefix}/" if prefix and not prefix.endswith("/") else prefix
        items = list_prefix(path)
        files = []
        sub_folders = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            if not name:
                continue
            if item.get("id"):
                # It's a file
                full_path = f"{path}{name}" if path else name
                pub_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{full_path}"
                metadata = item.get("metadata") or {}
                files.append({
                    "name": name,
                    "path": full_path,
                    "url": pub_url,
                    "size": metadata.get("size", 0),
                    "content_type": metadata.get("mimetype", "image/jpeg"),
                    "created_at": item.get("created_at", ""),
                })
            else:
                # It's a sub-folder
                sub_folders.append({"name": name, "path": f"{path}{name}"})

        return {
            "prefix": prefix,
            "files": files,
            "sub_folders": sub_folders,
            "total_files": len(files),
        }
    except Exception as e:
        raise HTTPException(500, str(e))
