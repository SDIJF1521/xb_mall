"""
平台端优惠券管理路由
- POST   /manage_coupon/create       创建平台优惠券
- POST   /manage_coupon/status       更新优惠券状态
- GET    /manage_coupon/list         优惠券列表
- GET    /manage_coupon/detail       优惠券详情
- POST   /manage_coupon/delete       删除优惠券
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query

from services.manage_admin_guard import verify_admin_with_permission
from services.promotion import PromotionService
from data.data_mods import CouponCreateBody, CouponStatusBody, CouponListQuery
from data.sql_client import get_db, execute_db_query
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_service(redis: RedisClient) -> PromotionService:
    return PromotionService(db_pool, redis)


@router.post("/manage_coupon/create")
async def create_coupon(
    data: Annotated[CouponCreateBody, Body()],
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端创建优惠券"""
    try:
        ok, msg, admin_info = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        svc = _get_service(redis)
        params = {
            "name": data.name,
            "coupon_type": data.coupon_type,
            "issuer_type": "platform",
            "discount_value": data.discount_value,
            "min_order_amount": data.min_order_amount,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "scope": data.scope,
            "platform_scope": data.platform_scope,
            "max_discount": data.max_discount,
            "total_count": data.total_count,
            "per_user_limit": data.per_user_limit,
            "description": data.description,
            "created_by": admin_info.get("user", "platform") if admin_info else "platform",
            "product_ids": [p.model_dump() for p in data.product_ids] if data.product_ids else None,
        }
        result = await svc.create_coupon(params)
        return {"current": True, **result}
    except Exception as e:
        logger.error("创建平台优惠券异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manage_coupon/status")
async def update_status(
    data: Annotated[CouponStatusBody, Body()],
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端更新优惠券状态"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        svc = _get_service(redis)
        result = await svc.update_coupon_status(data.coupon_id, data.status)
        return {"current": True, **result}
    except Exception as e:
        logger.error("更新优惠券状态异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manage_coupon/list")
async def coupon_list(
    data: CouponListQuery = Depends(),
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端获取优惠券列表（可查看所有优惠券）"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        svc = _get_service(redis)
        result = await svc.get_coupon_list(
            issuer_type=data.issuer_type,
            status=data.status,
            page=data.page,
            page_size=data.page_size,
        )
        return {"current": True, **result}
    except Exception as e:
        logger.error("查询优惠券列表异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manage_coupon/detail")
async def coupon_detail(
    coupon_id: int = Query(..., description="优惠券ID"),
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端获取优惠券详情"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        svc = _get_service(redis)
        result = await svc.get_coupon_detail(coupon_id)
        return {"current": True, **result}
    except Exception as e:
        logger.error("查询优惠券详情异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manage_coupon/delete")
async def delete_coupon(
    data: dict = Body(...),
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端删除优惠券"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        coupon_id = data.get("coupon_id")
        if not coupon_id:
            return {"current": True, "success": False, "msg": "缺少 coupon_id"}

        svc = _get_service(redis)
        result = await svc.delete_coupon(coupon_id)
        return {"current": True, **result}
    except Exception as e:
        logger.error("删除优惠券异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
