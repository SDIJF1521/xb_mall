"""GET /shopping_cart_list 获取当前用户购物车列表（分页 + 模糊搜索）"""
import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.user_info import UserInfo
from services.verify_duter_token import VerifyDuterToken
from data.file_client import read_file_base64_with_cache
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()

_PAGE_SIZE_DEFAULT = 10
_PAGE_SIZE_MAX = 50


async def _resolve_user(access_token: str, redis: RedisClient) -> str | None:
    """解析 token 获取用户标识"""
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    verify = VerifyDuterToken(access_token, redis)
    payload = await verify.token_data()
    if payload and payload.get("user"):
        return payload["user"]
    return None


@router.get("/shopping_cart_list")
async def shopping_cart_list(
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(10, ge=1, le=50, description="每页条数，最大 50"),
    search: str | None = Query(None, description="商品名称模糊搜索关键词"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取当前登录用户的购物车列表，支持分页和按商品名称模糊搜索"""
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False, "data": [], "total": 0}

    user = await _resolve_user(access_token, redis)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False, "data": [], "total": 0}

    search_kw = (search or "").strip()
    offset = (page - 1) * page_size

    # 构建查询：支持按 name 模糊搜索（需执行 migrations/add_shopping_cart_name.sql 添加 name 列）
    use_search = bool(search_kw)
    if use_search:
        count_sql = (
            "SELECT COUNT(*) FROM shopping_cart WHERE user = %s AND name LIKE %s"
        )
        list_sql = (
            "SELECT id, mall_id, shopping_id, specification_id, quantity FROM shopping_cart "
            "WHERE user = %s AND name LIKE %s ORDER BY id DESC LIMIT %s OFFSET %s"
        )
        like_param = f"%{search_kw}%"
        count_params = (user, like_param)
        list_params = (user, like_param, page_size, offset)
    else:
        count_sql = "SELECT COUNT(*) FROM shopping_cart WHERE user = %s"
        list_sql = (
            "SELECT id, mall_id, shopping_id, specification_id, quantity FROM shopping_cart "
            "WHERE user = %s ORDER BY id DESC LIMIT %s OFFSET %s"
        )
        count_params = (user,)
        list_params = (user, page_size, offset)

    try:
        count_rows = await db_pool.execute_query(count_sql, count_params)
        total = int(count_rows[0][0]) if count_rows else 0
    except Exception:
        if use_search:
            use_search = False
            count_sql = "SELECT COUNT(*) FROM shopping_cart WHERE user = %s"
            list_sql = (
                "SELECT id, mall_id, shopping_id, specification_id, quantity FROM shopping_cart "
                "WHERE user = %s ORDER BY id DESC LIMIT %s OFFSET %s"
            )
            count_params = (user,)
            list_params = (user, page_size, offset)
            count_rows = await db_pool.execute_query(count_sql, count_params)
            total = int(count_rows[0][0]) if count_rows else 0
        else:
            total = 0

    if total == 0:
        return {
            "code": 200,
            "msg": "成功",
            "success": True,
            "data": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
        }

    try:
        rows = await db_pool.execute_query(list_sql, list_params)
    except Exception:
        rows = []

    if not rows:
        return {
            "code": 200,
            "msg": "成功",
            "success": True,
            "data": [],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def _build_item(row: tuple) -> dict | None:
        cart_id, mall_id, shopping_id, specification_id, quantity = row
        doc = await mongodb.find_one(
            "shopping",
            {"mall_id": mall_id, "shopping_id": shopping_id},
        )
        if not doc:
            return {
                "id": cart_id,
                "mall_id": mall_id,
                "shopping_id": shopping_id,
                "name": "商品已下架",
                "img": "",
                "price": 0,
                "spec_text": "",
                "quantity": quantity,
                "stock": 0,
                "available": False,
            }

        spec_list = doc.get("specification_list") or []
        spec = next(
            (s for s in spec_list if s.get("specification_id") == specification_id),
            spec_list[0] if spec_list else {},
        )
        price = float(spec.get("price", 0))
        stock = int(spec.get("stock", 0))
        spec_text = " · ".join(spec.get("specs", [])) if spec.get("specs") else ""

        img_list = doc.get("img_list") or []
        img_b64 = ""
        if img_list:
            img_b64 = await read_file_base64_with_cache(img_list[0], redis, cache_expire=3600) or ""

        return {
            "id": cart_id,
            "mall_id": mall_id,
            "shopping_id": shopping_id,
            "name": doc.get("name", ""),
            "img": img_b64,
            "price": price,
            "spec_text": spec_text,
            "quantity": quantity,
            "stock": stock,
            "available": doc.get("audit") == 1,
        }

    results = await asyncio.gather(*[_build_item(r) for r in rows])
    items = [item for item in results if item is not None]

    return {
        "code": 200,
        "msg": "成功",
        "success": True,
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
