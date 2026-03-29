"""
C端用户优惠券路由
- GET   /user_coupon/available   可领取的优惠券列表
- POST  /user_coupon/claim       领取优惠券
- GET   /user_coupon/mine        我的优惠券列表
- GET   /user_coupon/usable      下单时可用的优惠券（按店铺和金额筛选）
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Header, Query, Body

from services.user_info import UserInfo
from services.promotion import PromotionService
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis

router = APIRouter()
logger = logging.getLogger(__name__)


async def _resolve_user(access_token: str) -> str | None:
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    return None


@router.get("/user_coupon/available")
async def available_coupons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    mall_id: int | None = Query(None, description="筛选店铺可用的优惠券"),
    shopping_id: int | None = Query(None, description="筛选指定商品可用的优惠券"),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
):
    """可领取的优惠券列表（无需登录即可浏览，登录后返回领取状态）"""
    try:
        user = None
        if access_token:
            user = await _resolve_user(access_token)
        svc = PromotionService(db_pool)
        result = await svc.get_available_coupons(
            page=page, page_size=page_size,
            mall_id=mall_id, shopping_id=shopping_id,
            user=user,
        )
        return {"code": 200, **result}
    except Exception as e:
        logger.error("获取可领优惠券列表异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


@router.post("/user_coupon/claim")
async def claim_coupon(
    data: dict = Body(...),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
):
    """领取优惠券"""
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    coupon_id = data.get("coupon_id")
    if not coupon_id:
        return {"code": 400, "msg": "缺少 coupon_id", "success": False}

    try:
        svc = PromotionService(db_pool)
        result = await svc.claim_coupon(user=user, coupon_id=int(coupon_id))
        return {"code": 200 if result["success"] else 400, **result}
    except Exception as e:
        logger.error("领取优惠券异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


@router.get("/user_coupon/mine")
async def my_coupons(
    status: str | None = Query(None, description="筛选状态：unused/used/expired"),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
):
    """我的优惠券列表"""
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    try:
        svc = PromotionService(db_pool)
        result = await svc.get_user_coupons(user=user, status=status)
        return {"code": 200, **result}
    except Exception as e:
        logger.error("获取我的优惠券异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


@router.get("/user_coupon/usable")
async def usable_coupons(
    mall_id: int = Query(..., ge=1, description="店铺ID"),
    order_amount: float = Query(..., gt=0, description="订单金额"),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
):
    """下单时可用的优惠券列表（按店铺和金额筛选）"""
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    try:
        svc = PromotionService(db_pool)
        result = await svc.get_usable_coupons(user=user, mall_id=mall_id, order_amount=order_amount)
        return {"code": 200, **result}
    except Exception as e:
        logger.error("获取可用优惠券异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}
