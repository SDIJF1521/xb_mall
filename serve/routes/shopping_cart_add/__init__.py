"""POST /shopping_cart_add 添加商品到购物车"""
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header

from services.user_info import UserInfo
from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.data_mods import ShoppingCartAddBody
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()


async def _resolve_user(access_token: str, redis: RedisClient) -> str | None:
    """解析 token 获取用户标识，支持 C 端 access_token 与商家端 buyer_access_token"""
    # 1. 尝试 C 端 token (JWT_USER_SECRET_KEY)
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    # 2. 尝试商家端 token (JWT_SELLER_SECRET_KEY)
    verify = VerifyDuterToken(access_token, redis)
    payload = await verify.token_data()
    if payload and payload.get("user"):
        return payload["user"]
    return None


@router.post("/shopping_cart_add")
async def shopping_cart_add(
    data: Annotated[ShoppingCartAddBody, Body()],
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """
    添加商品到购物车
    - 需登录，token 通过 access-token 请求头传递（支持 access_token / buyer_access_token）
    - 支持同规格合并：若购物车已有相同商品规格，则累加数量
    - 校验商品存在、上架、库存充足
    """
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}

    user = await _resolve_user(access_token, redis)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}
    mall_id = data.mall_id
    shopping_id = data.shopping_id
    spec_index = data.spec_index
    quantity = data.quantity

    # 1. 从 MongoDB 获取商品信息，校验商品存在且已上架
    doc = await mongodb.find_one(
        "shopping",
        {"mall_id": mall_id, "shopping_id": shopping_id, "audit": 1},
    )
    if not doc:
        return {"code": 404, "msg": "商品不存在或已下架", "success": False}

    spec_list = doc.get("specification_list") or []
    if spec_index >= len(spec_list):
        return {"code": 400, "msg": "无效的规格索引", "success": False}

    spec = spec_list[spec_index]
    specification_id = spec.get("specification_id")
    if specification_id is None:
        # 兼容：若 MongoDB 中无 specification_id，用索引作为 id（与 SQL specification 表可能不一致）
        specification_id = spec_index

    stock = int(spec.get("stock", 0))
    if stock < quantity:
        return {"code": 400, "msg": f"库存不足，当前仅剩 {stock} 件", "success": False}

    # 2. 查询购物车是否已有同款同规格
    exist_row = await db_pool.execute_query(
        "SELECT id, quantity FROM shopping_cart "
        "WHERE user = %s AND mall_id = %s AND shopping_id = %s AND specification_id = %s",
        (user, mall_id, shopping_id, specification_id),
    )

    if exist_row and len(exist_row) > 0:
        # 合并：累加数量，同步更新商品名称
        old_qty = int(exist_row[0][1])
        new_qty = old_qty + quantity
        if new_qty > stock:
            return {"code": 400, "msg": f"库存不足，当前仅剩 {stock} 件", "success": False}
        product_name = doc.get("name", "") or ""
        await db_pool.execute_query(
            "UPDATE shopping_cart SET quantity = %s, name = %s WHERE id = %s",
            (new_qty, product_name, exist_row[0][0]),
        )
    else:
        # 新增（存储商品名称供搜索）
        product_name = doc.get("name", "") or ""
        await db_pool.execute_query(
            "INSERT INTO shopping_cart (user, mall_id, shopping_id, specification_id, quantity, name) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user, mall_id, shopping_id, specification_id, quantity, product_name),
        )

    # 3. 清除购物车相关缓存（若有）
    cache = CacheService(redis)
    await cache.delete(cache._make_key("shopping_cart", user))

    return {"code": 200, "msg": "已加入购物车", "success": True}
