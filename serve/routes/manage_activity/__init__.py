"""
平台端活动管理路由
- POST   /manage_activity/create       创建平台活动
- POST   /manage_activity/status       更新活动状态
- GET    /manage_activity/list         活动列表
- GET    /manage_activity/detail       活动详情
- POST   /manage_activity/delete       删除活动
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query

from services.manage_admin_guard import verify_admin_with_permission
from services.promotion import PromotionService
from data.data_mods import ActivityCreateBody, ActivityStatusBody, ActivityListQuery
from data.sql_client import get_db, execute_db_query
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_service(redis: RedisClient) -> PromotionService:
    return PromotionService(db_pool, redis)


@router.post("/manage_activity/create")
async def create_activity(
    data: Annotated[ActivityCreateBody, Body()],
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端创建活动"""
    try:
        ok, msg, admin_info = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        svc = _get_service(redis)
        params = {
            "name": data.name,
            "activity_type": data.activity_type,
            "issuer_type": "platform",
            "start_time": data.start_time,
            "end_time": data.end_time,
            "rules": data.rules,
            "platform_scope": data.platform_scope,
            "description": data.description,
            "created_by": admin_info.get("user", "platform") if admin_info else "platform",
            "products": [p.model_dump() for p in data.products] if data.products else None,
            "coupon_ids": data.coupon_ids,
        }
        result = await svc.create_activity(params)
        return {"current": True, **result}
    except Exception as e:
        logger.error("创建平台活动异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manage_activity/status")
async def update_status(
    data: Annotated[ActivityStatusBody, Body()],
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端更新活动状态"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        svc = _get_service(redis)
        result = await svc.update_activity_status(data.activity_id, data.status)
        return {"current": True, **result}
    except Exception as e:
        logger.error("更新活动状态异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manage_activity/list")
async def activity_list(
    data: ActivityListQuery = Depends(),
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端获取活动列表（可查看所有活动）"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        svc = _get_service(redis)
        result = await svc.get_activity_list(
            issuer_type=data.issuer_type,
            activity_type=data.activity_type,
            status=data.status,
            page=data.page,
            page_size=data.page_size,
        )
        return {"current": True, **result}
    except Exception as e:
        logger.error("查询活动列表异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manage_activity/detail")
async def activity_detail(
    activity_id: int = Query(..., description="活动ID"),
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端获取活动详情"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        svc = _get_service(redis)
        result = await svc.get_activity_detail(activity_id)
        return {"current": True, **result}
    except Exception as e:
        logger.error("查询活动详情异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manage_activity/delete")
async def delete_activity(
    data: dict = Body(...),
    access_token: str = Header(...),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """平台端删除活动"""
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis, access_token, required="admin.promotion"
        )
        if not ok:
            return {"current": False, "msg": msg}

        activity_id = data.get("activity_id")
        if not activity_id:
            return {"current": True, "success": False, "msg": "缺少 activity_id"}

        svc = _get_service(redis)
        result = await svc.delete_activity(activity_id)
        return {"current": True, **result}
    except Exception as e:
        logger.error("删除活动异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
