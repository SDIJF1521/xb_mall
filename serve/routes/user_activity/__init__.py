"""
C端用户活动路由
- GET   /user_activity/list      进行中的活动列表
- GET   /user_activity/detail    活动详情（含活动商品）
"""

import logging

from fastapi import APIRouter, Query

from services.promotion import PromotionService
from data.sql_client_pool import db_pool

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/user_activity/list")
async def activity_list(
    activity_type: str | None = Query(None, description="活动类型：flash_sale/full_reduction/discount/group_buy"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    """进行中的活动列表（无需登录即可浏览）"""
    try:
        svc = PromotionService(db_pool)
        result = await svc.get_active_activities(
            activity_type=activity_type, page=page, page_size=page_size,
        )
        return {"code": 200, **result}
    except Exception as e:
        logger.error("获取活动列表异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


@router.get("/user_activity/detail")
async def activity_detail(
    activity_id: int = Query(..., ge=1, description="活动ID"),
):
    """活动详情（含活动商品列表）"""
    try:
        svc = PromotionService(db_pool)
        result = await svc.get_activity_detail(activity_id=activity_id)
        return {"code": 200 if result["success"] else 404, **result}
    except Exception as e:
        logger.error("获取活动详情异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}
