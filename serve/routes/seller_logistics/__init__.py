"""
卖家端物流管理路由
- POST /seller/order/ship           卖家发货
- GET  /seller/logistics/list       物流列表
- GET  /seller/logistics/detail     物流详情（含轨迹）
"""

import logging

from fastapi import APIRouter, Depends, Header, Query

from services.logistics import LogisticsService
from routes.seller_order import _verify_seller, _extract_mall_id
from data.data_mods import SellerShipOrderBody, LogisticsListQuery, LogisticsDetailQuery
from data.sql_client_pool import db_pool
from data.sql_client import get_db
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_logistics_svc(redis: RedisClient, mongodb: MongoDBClient) -> LogisticsService:
    return LogisticsService(db_pool, mongodb, redis)


# ──────────────────── 卖家发货 ────────────────────

@router.post("/seller/order/ship")
async def seller_ship_order(
    body: SellerShipOrderBody,
    mall_id: int | None = Query(None, description="指定店铺ID"),
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db, required_permissions=[1])
    if not ok:
        return {"success": False, "code": 403 if msg == "权限不足" else 401, "msg": msg}
    mall_id = _extract_mall_id(payload, mall_id)
    if not mall_id:
        return {"success": False, "msg": "无法确定所属店铺"}

    try:
        svc = _get_logistics_svc(redis, mongodb)
        result = await svc.ship_order(
            order_no=body.order_no,
            mall_id=mall_id,
            sender_name=body.sender_name,
            sender_phone=body.sender_phone,
            sender_address=body.sender_address,
            sender_post_code=body.sender_post_code,
        )
        return result
    except Exception as e:
        logger.error("卖家发货失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"发货失败: {str(e)}"}


# ──────────────────── 卖家物流列表 ────────────────────

@router.get("/seller/logistics/list")
async def seller_logistics_list(
    q: LogisticsListQuery = Depends(),
    mall_id: int | None = Query(None, description="指定店铺ID"),
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db, required_permissions=[2])
    if not ok:
        return {"success": False, "code": 403 if msg == "权限不足" else 401, "msg": msg}
    mall_id = _extract_mall_id(payload, mall_id)
    if not mall_id:
        return {"success": False, "msg": "无法确定所属店铺"}

    try:
        svc = _get_logistics_svc(redis, mongodb)
        return await svc.get_logistics_list(mall_id, q.keyword, q.page, q.page_size)
    except Exception as e:
        logger.error("物流列表查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


# ──────────────────── 卖家物流详情 ────────────────────

@router.get("/seller/logistics/detail")
async def seller_logistics_detail(
    q: LogisticsDetailQuery = Depends(),
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db, required_permissions=[2])
    if not ok:
        return {"success": False, "code": 403 if msg == "权限不足" else 401, "msg": msg}

    try:
        svc = _get_logistics_svc(redis, mongodb)
        return await svc.get_logistics_by_order(q.order_no)
    except Exception as e:
        logger.error("物流详情查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}
