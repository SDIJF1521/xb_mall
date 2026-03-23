import aiomysql
import jwt
from fastapi import APIRouter, Depends, HTTPException

from config.jwt_config import jwt_settings
from data.data_mods import ManageAdminRefreshBody
from data.redis_client import RedisClient, get_redis
from data.sql_client import get_db
from services.manage_token_issue import refresh_admin_tokens
from services.manage_rbac import get_user_permissions, get_user_role_row

router = APIRouter()


@router.post('/manage_admin_refresh')
async def manage_admin_refresh(
    body: ManageAdminRefreshBody,
    redis: RedisClient = Depends(get_redis),
    db: aiomysql.Connection = Depends(get_db),
):
    try:
        result = await refresh_admin_tokens(body.refresh_token, redis)
        if result.get("current") and result.get("access_token"):
            raw = result["access_token"]
            payload = jwt.decode(
                raw,
                jwt_settings.JWT_ADMIN_SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            user = payload.get("user")
            if user:
                result["permissions"] = await get_user_permissions(db, user)
                rr = await get_user_role_row(db, user)
                if rr:
                    result["role_id"] = rr[0]
                    result["role_name"] = rr[1]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
