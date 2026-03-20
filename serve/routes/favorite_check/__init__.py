"""GET /favorite_check 检查当前用户是否已收藏某商品或店铺"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.user_info import UserInfo
from data.sql_client_pool import db_pool

router = APIRouter()


async def _resolve_user(access_token: str) -> str | None:
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    return None


@router.get("/favorite_check")
async def favorite_check(
    type: str = Query(..., description="收藏类型：commodity 或 store"),
    mall_id: int = Query(..., ge=1, description="店铺ID"),
    shopping_id: int | None = Query(None, description="商品ID，收藏商品时必传"),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False, "is_favorited": False}

    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False, "is_favorited": False}

    if type == "commodity":
        rows = await db_pool.execute_query(
            "SELECT id FROM user_favorites "
            "WHERE user = %s AND type = 'commodity' AND mall_id = %s AND shopping_id = %s",
            (user, mall_id, shopping_id),
        )
    elif type == "store":
        rows = await db_pool.execute_query(
            "SELECT id FROM user_favorites "
            "WHERE user = %s AND type = 'store' AND mall_id = %s AND (shopping_id IS NULL OR shopping_id = 0)",
            (user, mall_id),
        )
    else:
        return {"code": 400, "msg": "type 必须为 commodity 或 store", "success": False, "is_favorited": False}

    is_fav = bool(rows and len(rows) > 0)
    fav_id = rows[0][0] if is_fav else None

    return {"code": 200, "msg": "成功", "success": True, "is_favorited": is_fav, "favorite_id": fav_id}
