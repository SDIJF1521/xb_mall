"""
用户端物流查询路由
- GET /order/logistics   查看订单物流信息及轨迹
"""

import logging

from fastapi import APIRouter, Depends, Header, Query

from services.user_info import UserInfo
from services.logistics import LogisticsService
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


async def _resolve_user(access_token: str) -> str | None:
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    return None


@router.get("/order/logistics")
async def order_logistics(
    order_no: str = Query(..., description="订单号"),
    access_token: str | None = Header(None, alias="access-token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    order_rows = await db_pool.execute_query(
        "SELECT user FROM orders WHERE order_no = %s", (order_no,)
    )
    if not order_rows or order_rows[0][0] != user:
        return {"code": 403, "msg": "无权查看此订单的物流信息", "success": False}

    try:
        svc = LogisticsService(db_pool, mongodb, redis)
        result = await svc.get_logistics_by_order(order_no)
        return {"code": 200 if result.get("success") else 404, **result}
    except Exception as e:
        logger.error("用户查询物流信息异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"查询失败: {str(e)}", "success": False}
