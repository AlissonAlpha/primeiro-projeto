from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
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


class DeleteRequest(BaseModel):
    paths: List[str]


def _delete_paths(paths: list) -> dict:
    """Delete files using Supabase Storage bulk delete API."""
    r = requests.delete(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}",
        headers=HEADERS,
        json={"prefixes": paths},
    )
    if r.status_code not in (200, 204):
        raise Exception(f"Supabase error {r.status_code}: {r.text}")
    return r.json()


def _list_all_files_in_folder(prefix: str) -> list:
    """Recursively list all files inside a folder prefix."""
    clean = prefix.rstrip("/") + "/"
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/list/{BUCKET}",
        headers=HEADERS,
        json={"prefix": clean, "limit": 1000},
    )
    items = r.json()
    paths = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        if not name:
            continue
        full = f"{clean}{name}"
        if item.get("id"):
            paths.append(full)
        else:
            # It's a sub-folder — recurse
            paths.extend(_list_all_files_in_folder(full))
    return paths


@router.delete("/files")
async def delete_files(body: DeleteRequest):
    """Delete one or more files from Supabase Storage."""
    try:
        _delete_paths(body.paths)
        return {"success": True, "deleted": len(body.paths)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/folder")
async def delete_folder(prefix: str):
    """Delete all files inside a folder (by prefix), including sub-folders."""
    try:
        paths = _list_all_files_in_folder(prefix)
        if not paths:
            return {"success": True, "deleted": 0, "message": "Pasta vazia ou não encontrada."}
        _delete_paths(paths)
        return {"success": True, "deleted": len(paths), "folder": prefix}
    except Exception as e:
        raise HTTPException(500, str(e))


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
