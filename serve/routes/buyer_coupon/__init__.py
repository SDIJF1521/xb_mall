"""
商家端优惠券管理路由
- POST   /buyer_coupon/create       创建商家优惠券（店铺/商品专属）
- POST   /buyer_coupon/status       更新优惠券状态
- GET    /buyer_coupon/list         本店优惠券列表
- GET    /buyer_coupon/detail       优惠券详情
- POST   /buyer_coupon/delete       删除优惠券
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Form, Header, HTTPException, Query

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.promotion import PromotionService
from data.data_mods import CouponCreateBody, CouponStatusBody, CouponListQuery
from data.sql_client import get_db, execute_db_query
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_service(redis: RedisClient) -> PromotionService:
    return PromotionService(db_pool, redis)


async def _verify_merchant(
    token: str, redis: RedisClient, db,
    require_write: bool = False,
    requested_mall_id: int | None = None,
) -> tuple[bool, str | None, dict | None]:
    """
    验证商家身份，兼容主商户(station=1)和店铺用户(station=2)。
    - station=1（店主）：查 seller_sing，mall_id 由前端指定（从 state_id_list 中选择）
    - station=2（店长/店员）：查 store_user + 角色权限，mall_id 从 token 中获取
    返回 (ok, error_msg, token_data)，token_data 中确保 mall_id 可用。
    """
    verify = VerifyDuterToken(token, redis)
    token_data = await verify.token_data()
    if not token_data:
        return False, "身份验证失败", None

    station = token_data.get("station")

    if station == "1":
        sql_data = await execute_db_query(
            db, "SELECT user FROM seller_sing WHERE user = %s", (token_data.get("user"),)
        )
        verify_val = await verify.verify_token(sql_data=sql_data)
        if not verify_val[0]:
            return False, "身份验证失败", None

        raw_list = token_data.get("state_id_list", [])
        state_id_list = [int(i) for i in raw_list if i]
        if not state_id_list:
            return False, "未找到店铺信息", None

        if requested_mall_id is not None:
            if requested_mall_id not in state_id_list:
                return False, "您没有权限操作该店铺", None
            token_data["mall_id"] = requested_mall_id
        else:
            token_data["mall_id"] = state_id_list[0]

    elif station == "2":
        user = token_data.get("user")
        mall_id = token_data.get("mall_id")
        sql_data = await execute_db_query(
            db, "SELECT user FROM store_user WHERE user = %s AND store_id = %s",
            (user, mall_id),
        )
        verify_val = await verify.verify_token(sql_data=sql_data)
        if not verify_val[0]:
            return False, "身份验证失败", None

        role_svc = RoleAuthorityService(
            role=token_data.get("role"), db=db, redis=redis,
            name=user, mall_id=mall_id,
        )
        role_authority = await role_svc.get_authority(mall_id)
        if not role_authority:
            return False, "未找到角色权限", None
        perms = await role_svc.authority_resolver(int(role_authority[0][0]))
        if not perms or not perms[2]:
            return False, "您没有查看营销管理的权限", None
        if require_write and (not perms[1]):
            return False, "您没有编辑营销内容的权限", None
    else:
        return False, "未知的身份类型", None

    return True, None, token_data


@router.post("/buyer_coupon/create")
async def create_coupon(
    data: Annotated[CouponCreateBody, Body()],
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端创建优惠券（只能创建本店铺的优惠券）"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, require_write=True, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mall_id = token_data.get("mall_id")
        if not mall_id:
            return {"current": False, "msg": "未找到店铺信息"}

        svc = _get_service(redis)
        params = {
            "name": data.name,
            "coupon_type": data.coupon_type,
            "issuer_type": "merchant",
            "discount_value": data.discount_value,
            "min_order_amount": data.min_order_amount,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "mall_id": int(mall_id),
            "scope": data.scope,
            "platform_scope": "all",
            "max_discount": data.max_discount,
            "total_count": data.total_count,
            "per_user_limit": data.per_user_limit,
            "description": data.description,
            "created_by": token_data.get("user"),
            "product_ids": [p.model_dump() for p in data.product_ids] if data.product_ids else None,
        }
        result = await svc.create_coupon(params)
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家创建优惠券异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer_coupon/status")
async def update_status(
    data: Annotated[CouponStatusBody, Body()],
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端更新优惠券状态（只能操作自己的优惠券）"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, require_write=True, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mall_id = token_data.get("mall_id")

        coupon_rows = await db_pool.execute_query(
            "SELECT mall_id FROM coupons WHERE id = %s", (data.coupon_id,)
        )
        if not coupon_rows:
            return {"current": True, "success": False, "msg": "优惠券不存在"}
        if str(coupon_rows[0][0]) != str(mall_id):
            return {"current": True, "success": False, "msg": "无权操作其他店铺的优惠券"}

        svc = _get_service(redis)
        result = await svc.update_coupon_status(data.coupon_id, data.status)
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家更新优惠券状态异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buyer_coupon/list")
async def coupon_list(
    data: CouponListQuery = Depends(),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端获取本店优惠券列表"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mall_id = token_data.get("mall_id")
        svc = _get_service(redis)
        result = await svc.get_coupon_list(
            issuer_type="merchant",
            mall_id=int(mall_id) if mall_id else None,
            status=data.status,
            page=data.page,
            page_size=data.page_size,
        )
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家查询优惠券列表异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buyer_coupon/detail")
async def coupon_detail(
    coupon_id: int = Query(..., description="优惠券ID"),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端获取优惠券详情"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        svc = _get_service(redis)
        result = await svc.get_coupon_detail(coupon_id)
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家查询优惠券详情异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer_coupon/delete")
async def delete_coupon(
    data: dict = Body(...),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端删除优惠券（只能删除本店铺的优惠券）"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, require_write=True, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        coupon_id = data.get("coupon_id")
        if not coupon_id:
            return {"current": True, "success": False, "msg": "缺少 coupon_id"}

        mall_id = token_data.get("mall_id")
        coupon_rows = await db_pool.execute_query(
            "SELECT mall_id FROM coupons WHERE id = %s", (coupon_id,)
        )
        if not coupon_rows:
            return {"current": True, "success": False, "msg": "优惠券不存在"}
        if str(coupon_rows[0][0]) != str(mall_id):
            return {"current": True, "success": False, "msg": "无权操作其他店铺的优惠券"}

        svc = _get_service(redis)
        result = await svc.delete_coupon(coupon_id)
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家删除优惠券异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
