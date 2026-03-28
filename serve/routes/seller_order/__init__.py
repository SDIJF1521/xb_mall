"""
卖家端订单与退款管理路由
- GET  /seller/order/list          订单列表
- GET  /seller/order/escrow_list   资金明细
- GET  /seller/order/refund_list   退款申请列表
- POST /seller/order/refund_review 退款审核
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from services.verify_duter_token import VerifyDuterToken
from services.refund import RefundService
from data.data_mods import SellerRefundReviewBody, SellerOrderListQuery, RefundListQuery
from data.sql_client import get_db, execute_db_query
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


async def _verify_seller(token: str, redis: RedisClient, db) -> tuple:
    """校验卖家 Token，返回 (ok, msg, token_payload_dict)"""
    verify = VerifyDuterToken(token, redis)
    token_data = await verify.token_data()
    if not token_data:
        return False, "Token 无效", None
    sql_data = await execute_db_query(
        db, "SELECT user FROM seller_sing WHERE user = %s", (token_data.get("user"),)
    )
    result = await verify.verify_token(sql_data=sql_data)
    if not result[0]:
        return False, "身份验证失败", None
    return True, "ok", token_data


def _extract_mall_id(payload: dict) -> int | None:
    station = payload.get("station")
    if station == "2":
        return payload.get("mall_id")
    id_list = payload.get("state_id_list")
    if id_list and isinstance(id_list, list) and len(id_list) > 0:
        return id_list[0]
    return None


@router.get("/seller/order/list")
async def seller_order_list(
    q: SellerOrderListQuery = Depends(),
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db)
    if not ok:
        return {"success": False, "msg": msg}
    mall_id = _extract_mall_id(payload)
    if not mall_id:
        return {"success": False, "msg": "无法确定所属店铺"}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.get_seller_order_list(mall_id, q.status, q.keyword, q.page, q.page_size)
    except Exception as e:
        logger.error("卖家订单列表查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


@router.get("/seller/order/escrow_list")
async def seller_escrow_list(
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db)
    if not ok:
        return {"success": False, "msg": msg}
    mall_id = _extract_mall_id(payload)
    if not mall_id:
        return {"success": False, "msg": "无法确定所属店铺"}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.get_seller_escrow_list(mall_id, status, page, page_size)
    except Exception as e:
        logger.error("卖家资金明细查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


@router.get("/seller/order/refund_list")
async def seller_refund_list(
    q: RefundListQuery = Depends(),
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db)
    if not ok:
        return {"success": False, "msg": msg}
    mall_id = _extract_mall_id(payload)
    if not mall_id:
        return {"success": False, "msg": "无法确定所属店铺"}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.get_refund_list_for_seller(mall_id, q.status, q.keyword, q.page, q.page_size)
    except Exception as e:
        logger.error("卖家退款列表查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


@router.post("/seller/order/refund_review")
async def seller_refund_review(
    body: SellerRefundReviewBody,
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db)
    if not ok:
        return {"success": False, "msg": msg}
    mall_id = _extract_mall_id(payload)
    if not mall_id:
        return {"success": False, "msg": "无法确定所属店铺"}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.seller_review(mall_id, body.refund_no, body.action, body.remark)
    except Exception as e:
        logger.error("卖家退款审核失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"操作失败: {str(e)}"}
