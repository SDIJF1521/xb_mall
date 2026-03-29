"""
商家端活动管理路由
- POST   /buyer_activity/create              创建商家活动
- POST   /buyer_activity/status              更新活动状态
- GET    /buyer_activity/list                本店活动列表
- GET    /buyer_activity/detail              活动详情
- POST   /buyer_activity/delete              删除活动
- GET    /buyer_activity/joinable            可加入的平台活动列表
- GET    /buyer_activity/shop_products       获取本店商品+规格列表（用于创建自有活动时选商品）
- GET    /buyer_activity/my_products         获取本店商品列表（用于选择加入平台活动）
- POST   /buyer_activity/join                加入平台活动（商家自选商品）
- POST   /buyer_activity/leave               退出平台活动
- GET    /buyer_activity/product_discounts   本店商品当前参与的所有生效折扣活动（估算用）
"""

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query

from services.verify_duter_token import VerifyDuterToken
from services.promotion import PromotionService
from data.data_mods import (
    ActivityCreateBody, ActivityStatusBody, ActivityListQuery,
    MerchantJoinActivityBody, MerchantLeaveActivityBody,
)
from data.sql_client import get_db, execute_db_query
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.file_client import read_file_base64_with_cache

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

        from services.buyer_role_authority import RoleAuthorityService
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


@router.post("/buyer_activity/create")
async def create_activity(
    data: Annotated[ActivityCreateBody, Body()],
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端创建活动"""
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
            "activity_type": data.activity_type,
            "issuer_type": "merchant",
            "start_time": data.start_time,
            "end_time": data.end_time,
            "rules": data.rules,
            "mall_id": int(mall_id),
            "platform_scope": "all",
            "description": data.description,
            "created_by": token_data.get("user"),
            "products": [p.model_dump() for p in data.products] if data.products else None,
            "coupon_ids": data.coupon_ids,
        }
        result = await svc.create_activity(params)
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家创建活动异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer_activity/status")
async def update_status(
    data: Annotated[ActivityStatusBody, Body()],
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端更新活动状态"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, require_write=True, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mall_id = token_data.get("mall_id")

        act_rows = await db_pool.execute_query(
            "SELECT mall_id FROM activities WHERE id = %s", (data.activity_id,)
        )
        if not act_rows:
            return {"current": True, "success": False, "msg": "活动不存在"}
        if str(act_rows[0][0]) != str(mall_id):
            return {"current": True, "success": False, "msg": "无权操作其他店铺的活动"}

        svc = _get_service(redis)
        result = await svc.update_activity_status(data.activity_id, data.status)
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家更新活动状态异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buyer_activity/list")
async def activity_list(
    data: ActivityListQuery = Depends(),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端获取本店活动列表"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mall_id = token_data.get("mall_id")
        svc = _get_service(redis)
        result = await svc.get_activity_list(
            issuer_type="merchant",
            mall_id=int(mall_id) if mall_id else None,
            activity_type=data.activity_type,
            status=data.status,
            page=data.page,
            page_size=data.page_size,
        )
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家查询活动列表异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buyer_activity/detail")
async def activity_detail(
    activity_id: int = Query(..., description="活动ID"),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端获取活动详情"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        svc = _get_service(redis)
        result = await svc.get_activity_detail(activity_id)
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家查询活动详情异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer_activity/delete")
async def delete_activity(
    data: dict = Body(...),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端删除活动"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, require_write=True, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        activity_id = data.get("activity_id")
        if not activity_id:
            return {"current": True, "success": False, "msg": "缺少 activity_id"}

        mall_id = token_data.get("mall_id")
        act_rows = await db_pool.execute_query(
            "SELECT mall_id FROM activities WHERE id = %s", (activity_id,)
        )
        if not act_rows:
            return {"current": True, "success": False, "msg": "活动不存在"}
        if str(act_rows[0][0]) != str(mall_id):
            return {"current": True, "success": False, "msg": "无权操作其他店铺的活动"}

        svc = _get_service(redis)
        result = await svc.delete_activity(activity_id)
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家删除活动异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buyer_activity/joinable")
async def joinable_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端获取可加入的平台活动列表"""
    try:
        ok, err, _ = await _verify_merchant(token, redis, db, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        svc = _get_service(redis)
        result = await svc.get_joinable_activities(page, page_size)
        return {"current": True, **result}
    except Exception as e:
        logger.error("查询可加入活动异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buyer_activity/shop_products")
async def shop_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    search: str = Query("", description="按商品名称搜索"),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取商家本店商品列表（含规格），用于创建店铺自有活动时选择商品"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mid = int(token_data.get("mall_id"))
        offset = (page - 1) * page_size

        mongo_filter: dict = {"mall_id": mid, "audit": 1}
        if search.strip():
            mongo_filter["name"] = {"$regex": search.strip(), "$options": "i"}

        total = await mongodb.count_documents("shopping", mongo_filter)
        docs = await mongodb.find_many(
            "shopping", mongo_filter,
            skip=offset, limit=page_size,
            sort=[("shopping_id", -1)],
        )

        async def _build(doc: dict) -> dict:
            img_b64 = ""
            if doc.get("img_list"):
                img_b64 = await read_file_base64_with_cache(doc["img_list"][0], redis, cache_expire=3600) or ""

            specs = []
            for sp in (doc.get("specification_list") or []):
                sid = sp.get("specification_id") or sp.get("id")
                # 规格名：优先 specs（字符串列表），其次 name 字段
                raw_specs = sp.get("specs") or []
                spec_name = " · ".join(raw_specs) if raw_specs else sp.get("name", "") or f"规格{sid}"
                specs.append({
                    "specification_id": sid,
                    "name": spec_name,
                    "price": float(sp.get("price", 0)),
                    "stock": int(sp.get("stock", 0)),
                })

            return {
                "shopping_id": doc["shopping_id"],
                "name": doc.get("name", ""),
                "img": img_b64,
                "specifications": specs,
            }

        items = await asyncio.gather(*[_build(d) for d in (docs or [])])
        return {
            "current": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": list(items),
        }
    except Exception as e:
        logger.error("获取店铺商品列表异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buyer_activity/my_products")
async def my_products(
    activity_id: int = Query(..., description="目标平台活动ID，用于过滤已加入的商品"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    search: str = Query("", description="按商品名称搜索"),
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取商家本店商品列表（含规格），供选择加入平台活动"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mid = int(token_data.get("mall_id"))
        offset = (page - 1) * page_size

        mongo_filter: dict = {"mall_id": mid, "audit": 1}
        if search.strip():
            mongo_filter["name"] = {"$regex": search.strip(), "$options": "i"}

        total = await mongodb.count_documents("shopping", mongo_filter)
        docs = await mongodb.find_many(
            "shopping", mongo_filter,
            skip=offset, limit=page_size,
            sort=[("shopping_id", -1)],
        )

        already_joined_rows = await db_pool.execute_query(
            """SELECT shopping_id, specification_id FROM activity_products
               WHERE activity_id = %s AND mall_id = %s AND status = 'active'""",
            (activity_id, mid),
        )
        joined_set = {(r[0], r[1]) for r in (already_joined_rows or [])}

        async def _build(doc: dict) -> dict:
            img_b64 = ""
            if doc.get("img_list"):
                img_b64 = await read_file_base64_with_cache(doc["img_list"][0], redis, cache_expire=3600) or ""

            specs = []
            for sp in (doc.get("specification_list") or []):
                sid = sp.get("specification_id") or sp.get("id")
                raw_specs = sp.get("specs") or []
                spec_name = " · ".join(raw_specs) if raw_specs else sp.get("name", "") or f"规格{sid}"
                specs.append({
                    "specification_id": sid,
                    "name": spec_name,
                    "price": float(sp.get("price", 0)),
                    "stock": sp.get("stock", 0),
                    "already_joined": (doc["shopping_id"], sid) in joined_set,
                })

            no_spec_joined = not specs and (doc["shopping_id"], None) in joined_set
            return {
                "shopping_id": doc["shopping_id"],
                "name": doc.get("name", ""),
                "img": img_b64,
                "specifications": specs,
                "already_joined": no_spec_joined,
            }

        items = await asyncio.gather(*[_build(d) for d in (docs or [])])
        return {
            "current": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": list(items),
        }
    except Exception as e:
        logger.error("获取商家商品列表异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer_activity/join")
async def join_activity(
    data: Annotated[MerchantJoinActivityBody, Body()],
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端将自选商品加入平台活动（mall_id 由 token 自动注入，无需前端填写）"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, require_write=True, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mid = token_data.get("mall_id")
        if not mid:
            return {"current": False, "msg": "未找到店铺信息"}

        svc = _get_service(redis)
        result = await svc.merchant_join_activity(
            activity_id=data.activity_id,
            mall_id=int(mid),
            products=[
                {
                    "shopping_id": p.shopping_id,
                    "specification_id": p.specification_id,
                    "activity_price": p.activity_price,
                    "activity_stock": p.activity_stock,
                }
                for p in data.products
            ],
        )
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家加入活动异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buyer_activity/leave")
async def leave_activity(
    data: Annotated[MerchantLeaveActivityBody, Body()],
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """商家端将商品从平台活动中移除"""
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, require_write=True, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mall_id = token_data.get("mall_id")
        if not mall_id:
            return {"current": False, "msg": "未找到店铺信息"}

        svc = _get_service(redis)
        result = await svc.merchant_leave_activity(
            activity_id=data.activity_id,
            mall_id=int(mall_id),
            shopping_ids=data.shopping_ids,
        )
        return {"current": True, **result}
    except Exception as e:
        logger.error("商家退出活动异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buyer_activity/product_discounts")
async def product_discounts(
    token: str = Header(..., alias="access-token"),
    mall_id: int | None = Query(None, description="店主指定操作的店铺ID"),
    db=Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """
    查询本店所有商品当前参与的生效折扣活动（秒杀/折扣/拼团）。
    返回按 shopping_id 分组的活动列表，前端用于创建活动时估算折上折价格。
    """
    try:
        ok, err, token_data = await _verify_merchant(token, redis, db, requested_mall_id=mall_id)
        if not ok:
            return {"current": False, "msg": err}

        mid = int(token_data.get("mall_id"))

        rows = await db_pool.execute_query(
            """SELECT ap.shopping_id, a.id AS activity_id, a.name AS activity_name,
                      a.activity_type, a.rules
               FROM activity_products ap
               JOIN activities a ON ap.activity_id = a.id
               WHERE ap.mall_id = %s
                 AND ap.status = 'active'
                 AND a.status = 'active'
                 AND NOW() BETWEEN a.start_time AND a.end_time
                 AND a.activity_type IN ('flash_sale', 'discount', 'group_buy')
               ORDER BY ap.shopping_id""",
            (mid,),
        )

        import json as _json
        product_map: dict[int, list] = {}
        for shopping_id, act_id, act_name, act_type, rules_raw in (rows or []):
            try:
                rules = _json.loads(rules_raw) if isinstance(rules_raw, str) else (rules_raw or {})
            except Exception:
                rules = {}
            dr = rules.get("discount_rate")
            if dr is None:
                continue
            product_map.setdefault(shopping_id, []).append({
                "activity_id": act_id,
                "activity_name": act_name,
                "activity_type": act_type,
                "discount_rate": float(dr),
            })

        return {"current": True, "success": True, "data": product_map}
    except Exception as e:
        logger.error("查询商品活动折扣异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
