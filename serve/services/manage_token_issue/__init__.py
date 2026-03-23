import secrets
from datetime import datetime, timedelta

import jwt

from config.jwt_config import jwt_settings
from data.redis_client import RedisClient

ACCESS_MINUTES = 120
REFRESH_DAYS = 7


async def issue_admin_tokens(user: str, redis_client: RedisClient) -> dict:
    access_expire = datetime.utcnow() + timedelta(minutes=ACCESS_MINUTES)
    access_ts = int(access_expire.timestamp())
    await redis_client.set(f"admin_{user}", str(access_ts))

    jti = secrets.token_urlsafe(32)
    await redis_client.setex(f"admin_refresh_{user}", REFRESH_DAYS * 86400, jti)

    refresh_expire = datetime.utcnow() + timedelta(days=REFRESH_DAYS)
    refresh_ts = int(refresh_expire.timestamp())

    secret = jwt_settings.JWT_ADMIN_SECRET_KEY
    access_payload = {"user": user, "exp": str(access_ts)}
    access_token = jwt.encode(access_payload, secret, algorithm="HS256")

    refresh_payload = {
        "user": user,
        "typ": "refresh",
        "jti": jti,
        "exp": str(refresh_ts),
    }
    refresh_token = jwt.encode(refresh_payload, secret, algorithm="HS256")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token": access_token,
        "token_type": "bearer",
    }


async def refresh_admin_tokens(refresh_token: str, redis_client: RedisClient) -> dict:
    from services.management_token_verify import _raw_jwt

    secret = jwt_settings.JWT_ADMIN_SECRET_KEY
    raw = _raw_jwt(refresh_token)
    payload = jwt.decode(
        raw, secret, algorithms=["HS256"],
        options={"verify_signature": True, "verify_exp": False},
    )
    if payload.get("typ") != "refresh":
        return {"current": False, "msg": "无效的 refresh_token"}
    user = payload.get("user")
    jti = payload.get("jti")
    if not user or not jti:
        return {"current": False, "msg": "无效的 refresh_token"}
    stored = await redis_client.get(f"admin_refresh_{user}")
    if stored != jti:
        return {"current": False, "msg": "refresh_token 已失效"}
    refresh_ts = int(payload.get("exp") or 0)
    if refresh_ts < int(datetime.utcnow().timestamp()):
        return {"current": False, "msg": "refresh_token 已过期"}
    tokens = await issue_admin_tokens(user, redis_client)
    return {"current": True, "msg": "刷新成功", **tokens}
