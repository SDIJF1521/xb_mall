"""GET /favorite_list 获取收藏列表（分页 + 模糊搜索 + 类型筛选）"""
import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from services.user_info import UserInfo
from data.data_mods import FavoriteListQuery
from data.file_client import read_file_base64_with_cache
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()


async def _resolve_user(access_token: str) -> str | None:
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    return None


@router.get("/favorite_list")
async def favorite_list(
    data: FavoriteListQuery = Depends(),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False, "data": [], "total": 0}

    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False, "data": [], "total": 0}

    page = data.page
    page_size = data.page_size
    fav_type = data.type
    search_kw = (data.search or "").strip()
    offset = (page - 1) * page_size

    where_clauses = ["user = %s"]
    params: list = [user]

    if fav_type in ("commodity", "store"):
        where_clauses.append("type = %s")
        params.append(fav_type)

    if search_kw:
        where_clauses.append("name LIKE %s")
        params.append(f"%{search_kw}%")

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) FROM user_favorites WHERE {where_sql}"
    count_rows = await db_pool.execute_query(count_sql, tuple(params))
    total = int(count_rows[0][0]) if count_rows else 0

    if total == 0:
        return {
            "code": 200, "msg": "成功", "success": True,
            "data": [], "total": 0, "page": page, "page_size": page_size,
        }

    list_sql = (
        f"SELECT id, type, mall_id, shopping_id, name, created_at "
        f"FROM user_favorites WHERE {where_sql} "
        f"ORDER BY id DESC LIMIT %s OFFSET %s"
    )
    list_params = tuple(params) + (page_size, offset)
    rows = await db_pool.execute_query(list_sql, list_params)

    if not rows:
        return {
            "code": 200, "msg": "成功", "success": True,
            "data": [], "total": total, "page": page, "page_size": page_size,
        }

    async def _build_commodity(row: tuple) -> dict:
        fav_id, _, mall_id, shopping_id, name, created_at = row
        doc = await mongodb.find_one(
            "shopping",
            {"mall_id": mall_id, "shopping_id": shopping_id},
        )
        if not doc:
            return {
                "id": fav_id, "type": "commodity",
                "mall_id": mall_id, "shopping_id": shopping_id,
                "name": name or "商品已下架", "img": "",
                "price": 0, "available": False,
                "created_at": str(created_at) if created_at else "",
            }

        spec_list = doc.get("specification_list") or []
        price = float(spec_list[0].get("price", 0)) if spec_list else 0

        img_list = doc.get("img_list") or []
        img_b64 = ""
        if img_list:
            img_b64 = await read_file_base64_with_cache(img_list[0], redis, cache_expire=3600) or ""

        return {
            "id": fav_id, "type": "commodity",
            "mall_id": mall_id, "shopping_id": shopping_id,
            "name": doc.get("name", name), "img": img_b64,
            "price": price, "available": doc.get("audit") == 1,
            "created_at": str(created_at) if created_at else "",
        }

    async def _build_store(row: tuple) -> dict:
        fav_id, _, mall_id, shopping_id, name, created_at = row
        store_rows = await db_pool.execute_query(
            "SELECT mall_name, img_path, mall_describe FROM store "
            "WHERE mall_id = %s",
            (mall_id,),
        )
        if not store_rows:
            return {
                "id": fav_id, "type": "store",
                "mall_id": mall_id, "shopping_id": None,
                "name": name or "店铺已关闭", "img": "",
                "info": "", "available": False,
                "created_at": str(created_at) if created_at else "",
            }

        s = store_rows[0]
        img_b64 = ""
        if s[1]:
            img_b64 = await read_file_base64_with_cache(s[1], redis, cache_expire=3600) or ""

        return {
            "id": fav_id, "type": "store",
            "mall_id": mall_id, "shopping_id": None,
            "name": s[0] or name, "img": img_b64,
            "info": s[2] or "", "available": True,
            "created_at": str(created_at) if created_at else "",
        }

    async def _build_item(row: tuple) -> dict:
        if row[1] == "commodity":
            return await _build_commodity(row)
        return await _build_store(row)

    results = await asyncio.gather(*[_build_item(r) for r in rows])

    return {
        "code": 200, "msg": "成功", "success": True,
        "data": list(results), "total": total,
        "page": page, "page_size": page_size,
    }
