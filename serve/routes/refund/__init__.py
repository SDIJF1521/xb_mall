"""
买家端退款路由
- POST /refund/apply         申请退款
- POST /refund/dispute       发起纠纷（申请平台介入）
- GET  /refund/detail        查看退款详情
- GET  /refund/by_order      查看订单的退款信息
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.user_info import UserInfo
from services.refund import RefundService
from data.data_mods import RefundApplyBody, RefundDisputeBody
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


async def _get_user(token: str) -> str | None:
    user_info = UserInfo(token)
    result = await user_info.token_analysis()
    if result.get("current"):
        return result["user"]
    return None


@router.post("/refund/apply")
async def refund_apply(
    body: RefundApplyBody,
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"success": False, "msg": "请先登录"}
    user = await _get_user(access_token)
    if not user:
        return {"success": False, "msg": "身份验证失败"}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.apply_refund(user, body.order_no, body.reason)
    except Exception as e:
        logger.error("退款申请失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"退款申请失败: {str(e)}"}


@router.post("/refund/dispute")
async def refund_dispute(
    body: RefundDisputeBody,
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"success": False, "msg": "请先登录"}
    user = await _get_user(access_token)
    if not user:
        return {"success": False, "msg": "身份验证失败"}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.buyer_dispute(user, body.refund_no)
    except Exception as e:
        logger.error("发起纠纷失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"操作失败: {str(e)}"}


@router.get("/refund/detail")
async def refund_detail(
    refund_no: str = Query(..., description="退款单号"),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"success": False, "msg": "请先登录"}
    user = await _get_user(access_token)
    if not user:
        return {"success": False, "msg": "身份验证失败"}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.get_refund_detail(refund_no)
    except Exception as e:
        logger.error("查询退款详情失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


@router.get("/refund/by_order")
async def refund_by_order(
    order_no: str = Query(..., description="订单号"),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"success": False, "msg": "请先登录"}
    user = await _get_user(access_token)
    if not user:
        return {"success": False, "msg": "身份验证失败"}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        data = await svc.get_refund_by_order(order_no)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error("查询订单退款信息失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}
