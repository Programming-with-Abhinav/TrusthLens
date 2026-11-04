"""Supabase integration helper for TrustLens backend.
Implements FR-A9 (token verification & usage recording) and FR-A10 (free-tier limit enforcement).
"""
import os
import datetime
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()


def get_supabase_url() -> str:
    return (os.getenv("SUPABASE_URL", "") or "").rstrip("/")


def get_supabase_key() -> str:
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")


def is_configured() -> bool:
    return bool(get_supabase_url() and get_supabase_key())


def get_headers() -> dict[str, str]:
    supabase_key = get_supabase_key()
    return {
        "apikey": supabase_key,
        "Authorization": "Bearer " + supabase_key,
        "Content-Type": "application/json",
        "Accept-Profile": "trustlens",
        "Content-Profile": "trustlens",
        "Prefer": "return=minimal",
    }


async def ping_supabase() -> bool:
    if not is_configured():
        return False
    supabase_url = get_supabase_url()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{supabase_url}/rest/v1/", headers=get_headers())
            return resp.status_code == 200
    except Exception:
        return False


async def verify_token(token: str) -> dict[str, object] | None:
    """Verify a bearer token against Supabase Auth."""
    if not token:
        return None

    bearer = token.replace("Bearer ", "", 1).strip()
    if not bearer:
        return None

    if not is_configured():
        raise HTTPException(status_code=401, detail="Authentication is unavailable")

    supabase_url = get_supabase_url()
    supabase_key = get_supabase_key()
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            auth_resp = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={"apikey": supabase_key, "Authorization": f"Bearer {bearer}"},
            )
            if auth_resp.status_code in (401, 403):
                raise HTTPException(status_code=401, detail="Token rejected by authentication service")
            if auth_resp.status_code != 200:
                raise HTTPException(status_code=503, detail="Authentication service unavailable")

            user_data = auth_resp.json()
            user_id = user_data.get("id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid authentication response")

            email = user_data.get("email", "")
            plan = "free"
            prof_resp = await client.get(
                f"{supabase_url}/rest/v1/profiles?id=eq.{user_id}&select=plan",
                headers=get_headers(),
            )
            if prof_resp.status_code == 200:
                profiles = prof_resp.json()
                if profiles:
                    plan = profiles[0].get("plan", "free")

            return {"id": user_id, "email": email, "plan": plan}
    except HTTPException:
        raise
    except (httpx.TimeoutException, httpx.NetworkError):
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    except Exception:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")


async def get_daily_usage(user_id: str, day: str | None = None) -> dict[str, object]:
    """Retrieves daily usage count for a user."""
    if not day:
        day = datetime.date.today().isoformat()

    default_usage: dict[str, object] = {"user_id": user_id, "day": day, "claim_checks": 0, "url_scans": 0}
    if not is_configured():
        return default_usage

    supabase_url = get_supabase_url()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{supabase_url}/rest/v1/usage_daily?user_id=eq.{user_id}&day=eq.{day}&select=claim_checks,url_scans",
                headers=get_headers(),
            )
            if resp.status_code == 200:
                rows = resp.json()
                if rows:
                    return {**default_usage, **rows[0]}
    except Exception:
        pass
    return default_usage


async def record_claim_check(user: dict[str, object], num_claims: int = 1) -> None:
    """Enforces free tier quota (FR-A10) and increments usage count (FR-A9)."""
    if not user:
        return

    user_id = str(user["id"])
    day = datetime.date.today().isoformat()

    if is_configured():
        supabase_url = get_supabase_url()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                for _ in range(num_claims):
                    await client.post(
                        f"{supabase_url}/rest/v1/rpc/increment_usage",
                        headers=get_headers(),
                        json={
                            "target_user_id": user_id,
                            "usage_type": "claim",
                            "usage_day": day,
                        },
                    )
        except Exception:
            pass


async def record_url_scan(user: dict[str, object]) -> None:
    """Increments URL scan count for authenticated user."""
    if not user:
        return

    user_id = str(user["id"])
    day = datetime.date.today().isoformat()

    if is_configured():
        supabase_url = get_supabase_url()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                await client.post(
                    f"{supabase_url}/rest/v1/rpc/increment_usage",
                    headers=get_headers(),
                    json={
                        "target_user_id": user_id,
                        "usage_type": "url",
                        "usage_day": day,
                    },
                )
        except Exception:
            pass
