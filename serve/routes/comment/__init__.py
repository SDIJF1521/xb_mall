"""
评论模块路由
- POST   /comment/create         发布评论（需登录、需购买且确认收货）
- POST   /comment/upload_images  上传评论图片（需登录）
- GET    /comment/list           获取商品评论列表（公开，支持好评/中评/差评筛选）
- GET    /comment/check          检查用户是否可以评论该商品（需登录）
- GET    /comment/user_list      获取用户自己的评论列表（需登录）
- DELETE /comment/delete         删除自己的评论（需登录）
- POST   /comment/seller_reply   卖家回复评论（需卖家Token）
- GET    /comment/seller_list    卖家获取店铺评论列表（需卖家Token）
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, Query, File, UploadFile, Form

from services.user_info import UserInfo
from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.comment import CommentService
from data.sql_client import get_db, execute_db_query
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_comment_service(redis: RedisClient, mongodb: MongoDBClient) -> CommentService:
    return CommentService(db_pool, redis, mongodb)


async def _resolve_user(access_token: str) -> str | None:
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    return None


async def _verify_seller(
    token: str, redis: RedisClient, db,
    required_permissions: list[int] | None = None,
) -> tuple:
    """
    校验卖家 Token，兼容主商户(station=1)和店铺用户(station=2)。
    station=1 主商户拥有全部权限，不做权限码检查。
    station=2 普通员工需要通过 RoleAuthorityService 检查操作权限码。
    required_permissions: 需要的权限索引列表 [0]=添加 [1]=写入 [2]=查询 [3]=删除 [4]=分配
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

        role_authority_service = RoleAuthorityService(
            role=token_data.get("role"),
            db=db,
            redis=redis,
            name=user,
            mall_id=mall_id,
        )
        role_authority = await role_authority_service.get_authority(mall_id)
        if not role_authority or not role_authority[0]:
            return False, "无法获取权限信息", None
        execute_code = await role_authority_service.authority_resolver(
            int(role_authority[0][0])
        )
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
    return int_list[0]


# ──────────────────── 发布评论 ────────────────────


@router.post("/comment/create")
async def create_comment(
    access_token: Annotated[str, Header(alias="access-token")],
    shopping_id: int = Form(..., description="商品ID"),
    mall_id: int = Form(..., description="店铺ID"),
    rating: int = Form(5, ge=1, le=5, description="评分 1-5"),
    content: str = Form(..., min_length=1, max_length=500, description="评论内容"),
    images: list[UploadFile] | None = File(None, description="评论图片（最多9张）"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """发布评论：需要购买过该商品且确认收货"""
    username = await _resolve_user(access_token)
    if not username:
        return {"code": 401, "msg": "请先登录", "success": False}

    image_bytes_list: list[bytes] = []
    if images:
        if len(images) > 9:
            return {"code": 400, "msg": "最多上传9张图片", "success": False}
        for img in images:
            img_data = await img.read()
            if len(img_data) > 5 * 1024 * 1024:
                return {"code": 400, "msg": f"图片 {img.filename} 超过5MB限制", "success": False}
            if img_data:
                image_bytes_list.append(img_data)

    svc = _get_comment_service(redis, mongodb)
    result = await svc.create_comment(
        username=username,
        shopping_id=shopping_id,
        mall_id=mall_id,
        rating=rating,
        content=content,
        images=image_bytes_list if image_bytes_list else None,
    )

    return {"code": 200 if result["success"] else 400, **result}


# ──────────────────── 获取商品评论列表（公开） ────────────────────


@router.get("/comment/list")
async def comment_list(
    shopping_id: int = Query(..., description="商品ID"),
    mall_id: int = Query(..., description="店铺ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页条数"),
    rating_type: Optional[str] = Query(None, description="评价类型: good/average/bad"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取商品评论列表，支持按好评/中评/差评筛选"""
    svc = _get_comment_service(redis, mongodb)
    return await svc.get_comment_list(
        shopping_id=shopping_id,
        mall_id=mall_id,
        page=page,
        page_size=page_size,
        rating_type=rating_type,
    )


# ──────────────────── 检查是否可评论 ────────────────────


@router.get("/comment/check")
async def check_commentable(
    access_token: Annotated[str, Header(alias="access-token")],
    shopping_id: int = Query(..., description="商品ID"),
    mall_id: int = Query(..., description="店铺ID"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """检查当前用户是否可以评论该商品"""
    username = await _resolve_user(access_token)
    if not username:
        return {"code": 401, "msg": "请先登录", "success": False}

    svc = _get_comment_service(redis, mongodb)
    result = await svc.check_commentable(username, shopping_id, mall_id)
    return {"code": 200, **result}


# ──────────────────── 用户评论列表 ────────────────────


@router.get("/comment/user_list")
async def user_comment_list(
    access_token: Annotated[str, Header(alias="access-token")],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页条数"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取当前用户的所有评论"""
    username = await _resolve_user(access_token)
    if not username:
        return {"code": 401, "msg": "请先登录", "success": False}

    svc = _get_comment_service(redis, mongodb)
    return await svc.get_user_comments(username, page, page_size)


# ──────────────────── 删除评论 ────────────────────


@router.delete("/comment/delete")
async def delete_comment(
    access_token: Annotated[str, Header(alias="access-token")],
    comment_id: str = Query(..., description="评论ID"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """删除自己的评论"""
    username = await _resolve_user(access_token)
    if not username:
        return {"code": 401, "msg": "请先登录", "success": False}

    svc = _get_comment_service(redis, mongodb)
    result = await svc.delete_comment(username, comment_id)
    return {"code": 200 if result["success"] else 400, **result}


# ──────────────────── 卖家按订单号获取评论（快捷回复用） ────────────────────


@router.get("/comment/order_comments")
async def order_comments(
    access_token: Annotated[str, Header(alias="Access-Token")],
    order_no: str = Query(..., description="订单号"),
    mall_id: int = Query(..., description="店铺ID"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    """卖家获取某个订单关联的所有评论"""
    ok, msg, payload = await _verify_seller(
        access_token, redis, db, required_permissions=[2]
    )
    if not ok:
        return {"code": 403 if msg == "权限不足" else 401, "msg": msg, "success": False}

    resolved_mall_id = _extract_mall_id(payload, mall_id)
    if resolved_mall_id is None:
        return {"code": 403, "msg": "无权操作该店铺", "success": False}

    svc = _get_comment_service(redis, mongodb)
    return await svc.get_comments_by_order(order_no, resolved_mall_id)


# ──────────────────── 卖家回复评论 ────────────────────


@router.post("/comment/seller_reply")
async def seller_reply(
    access_token: Annotated[str, Header(alias="Access-Token")],
    comment_id: str = Form(..., description="评论ID"),
    reply_content: str = Form(..., min_length=1, max_length=500, description="回复内容"),
    mall_id: int = Form(..., description="店铺ID"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    """卖家回复用户评论"""
    ok, msg, payload = await _verify_seller(
        access_token, redis, db, required_permissions=[1]
    )
    if not ok:
        return {"code": 403 if msg == "权限不足" else 401, "msg": msg, "success": False}

    resolved_mall_id = _extract_mall_id(payload, mall_id)
    if resolved_mall_id is None:
        return {"code": 403, "msg": "无权操作该店铺", "success": False}

    replied_by = payload.get("user", "卖家")

    svc = _get_comment_service(redis, mongodb)
    result = await svc.seller_reply(
        mall_id=resolved_mall_id,
        comment_id=comment_id,
        reply_content=reply_content,
        replied_by=replied_by,
    )
    return {"code": 200 if result["success"] else 400, **result}


# ──────────────────── 卖家评论列表 ────────────────────


@router.get("/comment/seller_list")
async def seller_comment_list(
    access_token: Annotated[str, Header(alias="Access-Token")],
    mall_id: int = Query(..., description="店铺ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页条数"),
    rating_type: Optional[str] = Query(None, description="评价类型: good/average/bad"),
    reply_status: Optional[str] = Query(None, description="回复状态: replied/unreplied"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    """卖家获取店铺下的所有评论，支持按评价等级和回复状态筛选"""
    ok, msg, payload = await _verify_seller(
        access_token, redis, db, required_permissions=[2]
    )
    if not ok:
        return {"code": 403 if msg == "权限不足" else 401, "msg": msg, "success": False}

    resolved_mall_id = _extract_mall_id(payload, mall_id)
    if resolved_mall_id is None:
        return {"code": 403, "msg": "无权操作该店铺", "success": False}

    svc = _get_comment_service(redis, mongodb)
    return await svc.get_seller_comments(
        mall_id=resolved_mall_id,
        page=page,
        page_size=page_size,
        rating_type=rating_type,
        reply_status=reply_status,
    )
