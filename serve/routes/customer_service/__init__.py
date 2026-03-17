"""
在线客服 WebSocket 路由。

端点：WS /api/ws/customer_service/{mall_id}?token=...&client_type=user|seller

服务端推送消息格式：

  [通用]
  - type=system      : { "type": "system", "content": "...", "created_at": "..." }

  [用户端]
  - type=history     : { "type": "history", "data": [...] }
  - type=chat        : { "type": "chat", "sender_type": "seller", "sender_name": "...",
                         "content": "...", "message_type": "text", "created_at": "..." }

  [卖家端]
  - type=session_list: { "type": "session_list", "data": [{session_id, online, last_message, last_time}] }
  - type=history     : { "type": "history", "session_id": "...", "data": [...] }
  - type=chat        : { "type": "chat", "session_id": "...", "sender_type": "user"|"seller",
                         "sender_name": "...", "content": "...", "message_type": "text"|"product_card",
                         "product_info": {...}?, "created_at": "..." }

客户端发送消息格式：

  [用户端]
  { "type": "chat", "content": "...", "message_type": "text"|"product_card",
    "product_info": {"name": "...", "spec": "...", "url": "...", "price": "..."}? }

  [卖家端]
  { "type": "chat", "content": "...", "target_session": "username" }
  { "type": "fetch_history", "session_id": "username" }
"""
import datetime
import json

from fastapi import APIRouter, Query, Depends, WebSocket, WebSocketDisconnect

from data.mongodb_client import get_mongodb_client, MongoDBClient
from data.redis_client import get_redis, RedisClient
from services.customer_service_manager import cs_manager
from services.customer_service_auth import CustomerServiceAuth

router = APIRouter()

COLLECTION = "customer_service_messages"
HISTORY_LIMIT = 80


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


async def _save_message(mongodb: MongoDBClient, doc: dict) -> None:
    try:
        await mongodb.insert_one(COLLECTION, doc)
    except Exception:
        pass


async def _get_session_history(mongodb: MongoDBClient, mall_id: int, session_id: str) -> list:
    try:
        return await mongodb.find_many(
            COLLECTION,
            {"mall_id": mall_id, "session_id": session_id},
            limit=HISTORY_LIMIT,
            sort=[("created_at", 1)],
        )
    except Exception:
        return []


async def _get_session_list(mongodb: MongoDBClient, mall_id: int) -> list:
    """获取该店铺的所有历史会话摘要（按最后消息时间降序）。"""
    try:
        pipeline = [
            {"$match": {"mall_id": mall_id}},
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$session_id",
                    "last_message": {"$first": "$content"},
                    "last_message_type": {"$first": "$message_type"},
                    "last_time": {"$first": "$created_at"},
                }
            },
            {"$sort": {"last_time": -1}},
            {"$limit": 100},
        ]
        result = await mongodb.aggregate(COLLECTION, pipeline)
        online_users = cs_manager.online_users(mall_id)
        sessions = []
        for item in result:
            session_id = item.get("_id", "")
            last_msg = item.get("last_message", "")
            if item.get("last_message_type") == "product_card":
                last_msg = "[商品] " + last_msg
            sessions.append({
                "session_id": session_id,
                "online": session_id in online_users,
                "last_message": last_msg,
                "last_time": item.get("last_time", ""),
            })
        return sessions
    except Exception:
        return []


# ── WebSocket 端点 ─────────────────────────────────────────────────────────────

@router.websocket("/ws/customer_service/{mall_id}")
async def customer_service_ws(
    websocket: WebSocket,
    mall_id: int,
    token: str = Query(..., description="JWT Token"),
    client_type: str = Query(..., description="连接类型：user（用户端）或 seller（卖家端）"),
    redis: RedisClient = Depends(get_redis),
):
    # ── 鉴权 ───────────────────────────────────────────────────────────────────
    auth = CustomerServiceAuth(token, client_type, redis)
    username = await auth.authenticate(mall_id)
    if username is None:
        await websocket.close(code=4001, reason="Token 无效或无权限")
        return

    if client_type not in ("user", "seller"):
        await websocket.close(code=4002, reason="client_type 参数错误")
        return

    mongodb: MongoDBClient = get_mongodb_client()

    if client_type == "user":
        await _handle_user(websocket, mall_id, username, mongodb)
    else:
        await _handle_seller(websocket, mall_id, username, mongodb)


# ── 用户端处理 ─────────────────────────────────────────────────────────────────

async def _handle_user(
    websocket: WebSocket, mall_id: int, username: str, mongodb: MongoDBClient
) -> None:
    await cs_manager.connect_user(websocket, mall_id, username)

    # 推送历史消息
    history = await _get_session_history(mongodb, mall_id, username)
    await websocket.send_json({"type": "history", "data": history})

    # 欢迎语
    await websocket.send_json({
        "type": "system",
        "content": "您已连接到在线客服，请描述您的问题",
        "created_at": _now(),
    })

    # 通知卖家端：该用户上线，推送更新后的会话列表
    session_list = await _get_session_list(mongodb, mall_id)
    await cs_manager.broadcast_to_sellers(mall_id, {
        "type": "session_list",
        "data": session_list,
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") != "chat":
                continue

            content: str = (msg.get("content") or "").strip()
            if not content or len(content) > 500:
                continue

            message_type: str = msg.get("message_type", "text")
            if message_type not in ("text", "product_card"):
                message_type = "text"

            product_info: dict | None = None
            if message_type == "product_card":
                product_info = msg.get("product_info")

            ts = _now()

            doc = {
                "mall_id": mall_id,
                "session_id": username,
                "sender_type": "user",
                "sender_name": username,
                "content": content,
                "message_type": message_type,
                "created_at": ts,
            }
            if product_info:
                doc["product_info"] = product_info

            await _save_message(mongodb, doc)

            # 回显给用户自身（确认消息已发出）
            await websocket.send_json({
                "type": "chat",
                "sender_type": "user",
                "sender_name": username,
                "content": content,
                "message_type": message_type,
                "product_info": product_info,
                "created_at": ts,
            })

            # 推送给所有在线卖家
            seller_msg = {
                "type": "chat",
                "session_id": username,
                "sender_type": "user",
                "sender_name": username,
                "content": content,
                "message_type": message_type,
                "created_at": ts,
            }
            if product_info:
                seller_msg["product_info"] = product_info
            await cs_manager.broadcast_to_sellers(mall_id, seller_msg)

    except WebSocketDisconnect:
        cs_manager.disconnect_user(mall_id, username)
        # 通知卖家端：用户下线，更新会话列表
        session_list = await _get_session_list(mongodb, mall_id)
        await cs_manager.broadcast_to_sellers(mall_id, {
            "type": "session_list",
            "data": session_list,
        })


# ── 卖家端处理 ─────────────────────────────────────────────────────────────────

async def _handle_seller(
    websocket: WebSocket, mall_id: int, username: str, mongodb: MongoDBClient
) -> None:
    await cs_manager.connect_seller(websocket, mall_id, username)

    # 推送当前会话列表
    session_list = await _get_session_list(mongodb, mall_id)
    await websocket.send_json({
        "type": "session_list",
        "data": session_list,
    })

    await websocket.send_json({
        "type": "system",
        "content": "客服系统已连接，等待用户咨询",
        "created_at": _now(),
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            # 卖家请求某会话的历史记录
            if msg_type == "fetch_history":
                session_id: str = msg.get("session_id", "").strip()
                if not session_id:
                    continue
                history = await _get_session_history(mongodb, mall_id, session_id)
                await websocket.send_json({
                    "type": "history",
                    "session_id": session_id,
                    "data": history,
                })
                continue

            # 卖家发送消息给某用户
            if msg_type == "chat":
                content: str = (msg.get("content") or "").strip()
                target_session: str = (msg.get("target_session") or "").strip()
                if not content or not target_session or len(content) > 500:
                    continue

                ts = _now()
                doc = {
                    "mall_id": mall_id,
                    "session_id": target_session,
                    "sender_type": "seller",
                    "sender_name": username,
                    "content": content,
                    "message_type": "text",
                    "created_at": ts,
                }
                await _save_message(mongodb, doc)

                # 转发给目标用户
                await cs_manager.send_to_user(mall_id, target_session, {
                    "type": "chat",
                    "sender_type": "seller",
                    "sender_name": "客服",
                    "content": content,
                    "message_type": "text",
                    "created_at": ts,
                })

                # 回显给卖家自身（确认）
                await websocket.send_json({
                    "type": "chat",
                    "session_id": target_session,
                    "sender_type": "seller",
                    "sender_name": username,
                    "content": content,
                    "message_type": "text",
                    "created_at": ts,
                })

    except WebSocketDisconnect:
        cs_manager.disconnect_seller(mall_id, username)
