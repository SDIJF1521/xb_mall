"""
客服消息 HTTP 接口。

- GET /cs_user_sessions：用户端获取所有客服会话列表（按店铺分组）
- GET /cs_user_history：用户端获取某店铺客服消息历史
- GET /cs_unread_count：获取未读消息数（用户端/卖家端）
- POST /cs_mark_read：标记已读
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, Query

from data.mongodb_client import get_mongodb_client, MongoDBClient
from data.data_mods import CsMarkReadBody
from data.redis_client import get_redis, RedisClient
from data.sql_client_pool import db_pool
from services.verify_duter_token import VerifyDuterToken
from services.customer_service_auth import CustomerServiceAuth

router = APIRouter()

COLLECTION = "customer_service_messages"

# Redis 未读 key 格式
# 用户端：cs_unread_user:{username}:{mall_id}
# 卖家端：cs_unread_seller:{mall_id}:{session_id}
# 卖家端某店铺总未读：需遍历该店铺所有 session 的 key 求和，或维护 cs_unread_seller_total:{mall_id}


def _user_unread_key(username: str, mall_id: int) -> str:
    return f"cs_unread_user:{username}:{mall_id}"


def _seller_unread_key(mall_id: int, session_id: str) -> str:
    return f"cs_unread_seller:{mall_id}:{session_id}"


# ── 用户端：获取会话列表 ───────────────────────────────────────────────────────

@router.get("/cs_user_sessions")
async def cs_user_sessions(
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    redis: RedisClient = Depends(get_redis),
):
    """
    用户端获取所有客服会话列表，按店铺分组。
    返回：[{ mall_id, mall_name, last_message, last_time, unread_count }, ...]
    """
    if not access_token:
        return {"current": False, "msg": "请先登录", "data": []}

    auth = CustomerServiceAuth(access_token, "user", redis)
    username = await auth.authenticate(0)  # mall_id 对 user 无影响
    if not username:
        return {"current": False, "msg": "Token 无效", "data": []}

    try:
        pipeline = [
            {"$match": {"session_id": username}},
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$mall_id",
                    "last_message": {"$first": "$content"},
                    "last_message_type": {"$first": "$message_type"},
                    "last_time": {"$first": "$created_at"},
                }
            },
            {"$sort": {"last_time": -1}},
        ]
        result = await mongodb.aggregate(COLLECTION, pipeline)
    except Exception:
        return {"current": False, "msg": "查询失败", "data": []}

    sessions = []
    for item in result:
        mall_id = item.get("_id")
        if mall_id is None:
            continue
        last_msg = item.get("last_message", "")
        if item.get("last_message_type") == "product_card":
            last_msg = "[商品] " + last_msg
        unread = await redis.get_int(_user_unread_key(username, mall_id))

        # 获取店铺名称
        mall_name = ""
        try:
            rows = await db_pool.execute_query(
                "SELECT mall_name FROM store WHERE mall_id = %s", (mall_id,)
            )
            if rows:
                mall_name = rows[0][0] or ""
        except Exception:
            pass

        sessions.append({
            "mall_id": mall_id,
            "mall_name": mall_name or f"店铺{mall_id}",
            "last_message": last_msg,
            "last_time": item.get("last_time", ""),
            "unread_count": unread,
        })

    return {"current": True, "msg": "成功", "data": sessions}


# ── 用户端：获取某店铺消息历史 ──────────────────────────────────────────────────

@router.get("/cs_user_history")
async def cs_user_history(
    mall_id: int = Query(..., ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    redis: RedisClient = Depends(get_redis),
):
    """用户端获取与某店铺的客服消息历史，分页。"""
    if not access_token:
        return {"current": False, "msg": "请先登录", "data": [], "total": 0}

    auth = CustomerServiceAuth(access_token, "user", redis)
    username = await auth.authenticate(0)
    if not username:
        return {"current": False, "msg": "Token 无效", "data": [], "total": 0}

    try:
        total = await mongodb.count_documents(
            COLLECTION,
            {"mall_id": mall_id, "session_id": username},
        )
        skip = (page - 1) * page_size
        docs = await mongodb.find_many(
            COLLECTION,
            {"mall_id": mall_id, "session_id": username},
            skip=skip,
            limit=page_size,
            sort=[("created_at", -1)],
        )
        # 按时间正序返回（旧→新）
        docs = list(reversed(docs))
    except Exception:
        return {"current": False, "msg": "查询失败", "data": [], "total": 0}

    # 标记已读（用户打开该会话时清零）
    await redis.delete(_user_unread_key(username, mall_id))

    data = []
    for d in docs:
        data.append({
            "sender_type": d.get("sender_type", ""),
            "sender_name": d.get("sender_name", ""),
            "content": d.get("content", ""),
            "message_type": d.get("message_type", "text"),
            "product_info": d.get("product_info"),
            "created_at": d.get("created_at", ""),
        })

    return {"current": True, "msg": "成功", "data": data, "total": total}


# ── 获取未读数量 ──────────────────────────────────────────────────────────────

@router.get("/cs_unread_count")
async def cs_unread_count(
    role: str = Query(..., description="user 或 seller"),
    mall_id: Optional[int] = Query(None, ge=1),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
):
    """
    获取未读消息数。
    - role=user：返回该用户所有店铺未读总和（不传 mall_id）
    - role=seller：mall_id 必传，返回该店铺所有用户发来的未读总和
    """
    if not access_token:
        return {"current": False, "msg": "请先登录", "unread_count": 0}

    if role == "user":
        auth = CustomerServiceAuth(access_token, "user", redis)
        username = await auth.authenticate(0)
        if not username:
            return {"current": False, "msg": "Token 无效", "unread_count": 0}
        # 用户端：mall_id 可选，不传则返回所有店铺未读总和，传则只返回该店铺未读
        try:
            if mall_id:
                total = await redis.get_int(_user_unread_key(username, mall_id))
            else:
                from data.mongodb_client import get_mongodb_client
                mongodb = get_mongodb_client()
                pipeline = [
                    {"$match": {"session_id": username}},
                    {"$group": {"_id": "$mall_id"}},
                ]
                result = await mongodb.aggregate(COLLECTION, pipeline)
                total = 0
                for item in result:
                    mid = item.get("_id")
                    if mid:
                        total += await redis.get_int(_user_unread_key(username, mid))
            return {"current": True, "msg": "成功", "unread_count": total}
        except Exception:
            return {"current": False, "msg": "查询失败", "unread_count": 0}

    elif role == "seller":
        if not mall_id:
            return {"current": False, "msg": "卖家端需传 mall_id", "unread_count": 0}
        auth = CustomerServiceAuth(access_token, "seller", redis)
        _ = await auth.authenticate(mall_id)
        if not _:
            return {"current": False, "msg": "Token 无效或无权限", "unread_count": 0}
        # 卖家端：遍历该店铺所有 session 的未读
        try:
            from data.mongodb_client import get_mongodb_client
            mongodb = get_mongodb_client()
            pipeline = [
                {"$match": {"mall_id": mall_id}},
                {"$group": {"_id": "$session_id"}},
            ]
            result = await mongodb.aggregate(COLLECTION, pipeline)
            total = 0
            for item in result:
                sid = item.get("_id")
                if sid:
                    total += await redis.get_int(_seller_unread_key(mall_id, sid))
            return {"current": True, "msg": "成功", "unread_count": total}
        except Exception:
            return {"current": False, "msg": "查询失败", "unread_count": 0}

    return {"current": False, "msg": "role 参数错误", "unread_count": 0}


# ── 卖家端：获取所有店铺总未读（用于导航徽章）────────────────────────────────────

@router.get("/cs_seller_total_unread")
async def cs_seller_total_unread(
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
):
    """
    卖家端获取所有有权限店铺的客服未读消息总和，用于导航栏徽章。
    """
    if not access_token:
        return {"current": False, "msg": "请先登录", "unread_count": 0}

    try:
        from services.verify_duter_token import VerifyDuterToken
        verifier = VerifyDuterToken(access_token, redis)
        token_data = await verifier.token_data()
        if not token_data:
            return {"current": False, "msg": "Token 无效", "unread_count": 0}

        mall_ids = []
        if token_data.get("station") == "1":
            mall_ids = list(token_data.get("state_id_list") or [])
        elif token_data.get("station") == "2":
            mid = token_data.get("mall_id")
            if mid is not None:
                mall_ids = [mid]

        if not mall_ids:
            return {"current": True, "msg": "成功", "unread_count": 0}

        from data.mongodb_client import get_mongodb_client
        mongodb = get_mongodb_client()
        total = 0
        for mall_id in mall_ids:
            pipeline = [
                {"$match": {"mall_id": mall_id}},
                {"$group": {"_id": "$session_id"}},
            ]
            result = await mongodb.aggregate(COLLECTION, pipeline)
            for item in result:
                sid = item.get("_id")
                if sid:
                    total += await redis.get_int(_seller_unread_key(mall_id, sid))

        return {"current": True, "msg": "成功", "unread_count": total}
    except Exception:
        return {"current": False, "msg": "查询失败", "unread_count": 0}


# ── 卖家端：获取每个店铺的未读明细（用于店铺选择页徽章）──────────────────────

@router.get("/cs_seller_store_unreads")
async def cs_seller_store_unreads(
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
):
    """
    卖家端获取每个有权限店铺的客服未读消息数，
    返回 { current, data: [{ mall_id, unread_count }] }，用于店铺选择页展示徽章。
    """
    if not access_token:
        return {"current": False, "msg": "请先登录", "data": []}

    try:
        verifier = VerifyDuterToken(access_token, redis)
        token_data = await verifier.token_data()
        if not token_data:
            return {"current": False, "msg": "Token 无效", "data": []}

        mall_ids = []
        if token_data.get("station") == "1":
            mall_ids = list(token_data.get("state_id_list") or [])
        elif token_data.get("station") == "2":
            mid = token_data.get("mall_id")
            if mid is not None:
                mall_ids = [mid]

        if not mall_ids:
            return {"current": True, "msg": "成功", "data": []}

        from data.mongodb_client import get_mongodb_client
        mongodb = get_mongodb_client()
        result_list = []
        for mall_id in mall_ids:
            pipeline = [
                {"$match": {"mall_id": mall_id}},
                {"$group": {"_id": "$session_id"}},
            ]
            result = await mongodb.aggregate(COLLECTION, pipeline)
            total = 0
            for item in result:
                sid = item.get("_id")
                if sid:
                    total += await redis.get_int(_seller_unread_key(mall_id, sid))
            if total > 0:
                result_list.append({"mall_id": mall_id, "unread_count": total})

        return {"current": True, "msg": "成功", "data": result_list}
    except Exception:
        return {"current": False, "msg": "查询失败", "data": []}


# ── 标记已读 ───────────────────────────────────────────────────────────────────

@router.post("/cs_mark_read")
async def cs_mark_read(
    body: CsMarkReadBody,
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
):
    """
    标记已读。
    - role=user：将用户在该店铺的未读清零，不需 session_id
    - role=seller：将卖家在该店铺某会话的未读清零，需传 session_id
    """
    if not access_token:
        return {"current": False, "msg": "请先登录"}

    mall_id = body.mall_id
    role = body.role
    session_id = body.session_id

    if role == "user":
        auth = CustomerServiceAuth(access_token, "user", redis)
        username = await auth.authenticate(0)
        if not username:
            return {"current": False, "msg": "Token 无效"}
        await redis.delete(_user_unread_key(username, mall_id))
        return {"current": True, "msg": "已标记已读"}

    elif role == "seller":
        if not session_id:
            return {"current": False, "msg": "卖家端需传 session_id"}
        auth = CustomerServiceAuth(access_token, "seller", redis)
        _ = await auth.authenticate(mall_id)
        if not _:
            return {"current": False, "msg": "Token 无效或无权限"}
        await redis.delete(_seller_unread_key(mall_id, session_id))
        return {"current": True, "msg": "已标记已读"}

    return {"current": False, "msg": "role 参数错误"}
