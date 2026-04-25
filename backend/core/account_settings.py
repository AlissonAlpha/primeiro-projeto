import httpx
from typing import Optional
from .config import settings

SUPABASE_URL = settings.SUPABASE_URL
HEADERS = {
    "apikey": settings.SUPABASE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


async def get_account_settings(ad_account_id: str) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SUPABASE_URL}/rest/v1/account_settings",
            headers=HEADERS,
            params={"ad_account_id": f"eq.{ad_account_id}", "limit": "1"},
        )
        data = r.json()
        return data[0] if data else None


async def save_account_settings(ad_account_id: str, account_name: str, **kwargs) -> dict:
    payload = {"ad_account_id": ad_account_id, "account_name": account_name, **kwargs}
    async with httpx.AsyncClient() as client:
        # Upsert
        r = await client.post(
            f"{SUPABASE_URL}/rest/v1/account_settings",
            headers={**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"},
            json=payload,
        )
        data = r.json()
        return data[0] if isinstance(data, list) and data else data


def get_account_settings_sync(ad_account_id: str) -> Optional[dict]:
    import httpx
    with httpx.Client() as client:
        r = client.get(
            f"{SUPABASE_URL}/rest/v1/account_settings",
            headers=HEADERS,
            params={"ad_account_id": f"eq.{ad_account_id}", "limit": "1"},
        )
        data = r.json()
        return data[0] if data else None


def save_account_settings_sync(ad_account_id: str, account_name: str = "", **kwargs) -> dict:
    import httpx
    payload = {"ad_account_id": ad_account_id, "account_name": account_name, **kwargs}
    with httpx.Client() as client:
        r = client.post(
            f"{SUPABASE_URL}/rest/v1/account_settings",
            headers={**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"},
            json=payload,
        )
        data = r.json()
        return data[0] if isinstance(data, list) and data else data
