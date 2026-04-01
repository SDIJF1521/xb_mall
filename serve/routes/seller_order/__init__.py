"""
卖家端订单与退款管理路由
- GET  /seller/order/list          订单列表
- GET  /seller/order/escrow_list   资金明细
- GET  /seller/order/refund_list   退款申请列表
- POST /seller/order/refund_review 退款审核
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.refund import RefundService
from data.data_mods import SellerRefundReviewBody, SellerOrderListQuery, RefundListQuery
from data.sql_client import get_db, execute_db_query
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


async def _verify_seller(
    token: str, redis: RedisClient, db,
    required_permissions: list[int] | None = None,
) -> tuple:
    """
    校验卖家 Token，兼容主商户(station=1)和店铺用户(station=2)。
    station=2 普通员工通过 RoleAuthorityService 检查操作权限码。
    required_permissions: [0]=添加 [1]=写入 [2]=查询 [3]=删除 [4]=分配
    """
    verify = VerifyDuterToken(token, redis)
    token_data = await verify.token_data()
    if not token_data:
        return False, "Token 无效", None

    station = token_data.get("station")

    if station == "1":
        sql_data = await execute_db_query(
            db, "SELECT user FROM seller_sing WHERE user = %s", (token_data.get("user"),)
        )
        result = await verify.verify_token(sql_data=sql_data)
        if not result[0]:
            return False, "身份验证失败", None

        raw_list = token_data.get("state_id_list", [])
        state_id_list = [int(i) for i in raw_list if i]
        if not state_id_list:
            return False, "未找到店铺信息", None
        token_data["_state_id_list"] = state_id_list
        if token_data.get("mall_id") is None:
            token_data["mall_id"] = state_id_list[0]

    elif station == "2":
        user = token_data.get("user")
        mall_id = token_data.get("mall_id")

        role_svc = RoleAuthorityService(
            role=token_data.get("role"), db=db, redis=redis,
            name=user, mall_id=mall_id,
        )
        role_authority = await role_svc.get_authority(mall_id)
        if not role_authority or not role_authority[0]:
            return False, "无法获取权限信息", None
        execute_code = await role_svc.authority_resolver(int(role_authority[0][0]))
        if not execute_code:
            return False, "权限解析失败", None

        if required_permissions:
            for perm_idx in required_permissions:
                if perm_idx >= len(execute_code) or not execute_code[perm_idx]:
                    return False, "权限不足", None

        sql_data = await execute_db_query(
            db, "SELECT user FROM store_user WHERE user = %s AND store_id = %s",
            (user, mall_id),
        )
        result = await verify.verify_token(sql_data=sql_data)
        if not result[0]:
            return False, "身份验证失败", None
    else:
        return False, "未知的身份类型", None

    return True, "ok", token_data


def _extract_mall_id(payload: dict, requested_mall_id: int | None = None) -> int | None:
    station = payload.get("station")
    if station == "2":
        mid = payload.get("mall_id")
        return int(mid) if mid is not None else None

    id_list = payload.get("_state_id_list") or payload.get("state_id_list")
    if not id_list or not isinstance(id_list, list) or len(id_list) == 0:
        return None
    int_list = [int(i) for i in id_list if i]
    if requested_mall_id is not None:
        if requested_mall_id in int_list:
            return requested_mall_id
        return None
    return int_list[0] if int_list else None


@router.get("/seller/order/list")
async def seller_order_list(
    q: SellerOrderListQuery = Depends(),
    mall_id: int | None = Query(None, description="指定店铺ID（主账号多店铺时使用）"),
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
    mall_id: int | None = Query(None, description="指定店铺ID（主账号多店铺时使用）"),
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
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.get_seller_escrow_list(mall_id, status, page, page_size)
    except Exception as e:
        logger.error("卖家资金明细查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


@router.get("/seller/order/refund_list")
async def seller_refund_list(
    q: RefundListQuery = Depends(),
    mall_id: int | None = Query(None, description="指定店铺ID（主账号多店铺时使用）"),
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
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.get_refund_list_for_seller(mall_id, q.status, q.keyword, q.page, q.page_size)
    except Exception as e:
        logger.error("卖家退款列表查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


@router.post("/seller/order/refund_review")
async def seller_refund_review(
    body: SellerRefundReviewBody,
    mall_id: int | None = Query(None, description="指定店铺ID（主账号多店铺时使用）"),
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
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.seller_review(mall_id, body.refund_no, body.action, body.remark)
    except Exception as e:
        logger.error("卖家退款审核失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"操作失败: {str(e)}"}
