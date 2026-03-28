"""
平台端纠纷管理路由
- GET  /manage/refund/list       纠纷列表
- GET  /manage/refund/detail     退款详情
- POST /manage/refund/resolve    仲裁操作
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.manage_admin_guard import verify_admin_with_permission
from services.refund import RefundService
from data.data_mods import PlatformRefundResolveBody, RefundListQuery
from data.sql_client import get_db
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)

REQUIRED_PERMISSION = "admin.refund"


@router.get("/manage/refund/list")
async def manage_refund_list(
    q: RefundListQuery = Depends(),
    access_token: Annotated[str | None, Header(alias="Access-Token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    if not access_token:
        return {"success": False, "msg": "请先登录"}
    ok, msg, admin = await verify_admin_with_permission(db, redis, access_token, required=REQUIRED_PERMISSION)
    if not ok:
        return {"success": False, "msg": msg}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.get_refund_list_for_platform(q.status, q.keyword, q.page, q.page_size)
    except Exception as e:
        logger.error("平台纠纷列表查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


@router.get("/manage/refund/detail")
async def manage_refund_detail(
    refund_no: str = Query(..., description="退款单号"),
    access_token: Annotated[str | None, Header(alias="Access-Token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    if not access_token:
        return {"success": False, "msg": "请先登录"}
    ok, msg, admin = await verify_admin_with_permission(db, redis, access_token, required=REQUIRED_PERMISSION)
    if not ok:
        return {"success": False, "msg": msg}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.get_refund_detail(refund_no)
    except Exception as e:
        logger.error("平台退款详情查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


@router.post("/manage/refund/resolve")
async def manage_refund_resolve(
    body: PlatformRefundResolveBody,
    access_token: Annotated[str | None, Header(alias="Access-Token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    if not access_token:
        return {"success": False, "msg": "请先登录"}
    ok, msg, admin = await verify_admin_with_permission(db, redis, access_token, required=REQUIRED_PERMISSION)
    if not ok:
        return {"success": False, "msg": msg}
    try:
        svc = RefundService(db_pool, mongodb, redis)
        return await svc.platform_resolve(admin, body.refund_no, body.action, body.remark)
    except Exception as e:
        logger.error("平台仲裁失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"操作失败: {str(e)}"}
