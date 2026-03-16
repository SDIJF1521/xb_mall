import json
import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends

from data.redis_client import RedisClient, get_redis
from data.mongodb_client import get_mongodb_client, MongoDBClient
from services.store_chat_manager import store_manager
from services.store_chat_auth import StoreChatAuth

router = APIRouter()

COLLECTION = "store_employee_chat"
HISTORY_LIMIT = 80


@router.websocket("/ws/store_chat/{mall_id}")
async def store_chat_ws(
    websocket: WebSocket,
    mall_id: int,
    token: str = Query(..., description="商户端 JWT Token（格式同其他卖家端接口，可带 bearer 前缀）"),
    redis: RedisClient = Depends(get_redis),
):
    """
    店铺内员工实时聊天 WebSocket 端点。

    服务端推送消息格式：
      - type=history : { "type": "history", "data": [...] }
      - type=chat    : { "type": "chat", "username": "...", "content": "...", "created_at": "..." }
      - type=system  : { "type": "system", "content": "...", "online_users": [...], "created_at": "..." }

    客户端发送消息格式：
      { "type": "chat", "content": "..." }
    """
    # ── 鉴权（StoreChatAuth 服务层）─────────────────────────────────────────
    username = await StoreChatAuth(token, redis).authenticate(mall_id)
    if username is None:
        await websocket.close(code=4001, reason="Token 无效或无权限访问该店铺聊天室")
        return

    # ── 建立连接（StoreConnectionManager 服务层）────────────────────────────
    await store_manager.connect(websocket, mall_id, username)
    mongodb: MongoDBClient = get_mongodb_client()
    now_str = datetime.datetime.now().isoformat(timespec="seconds")

    # 推送历史消息给新连接的用户
    try:
        history = await mongodb.find_many(
            COLLECTION,
            {"mall_id": mall_id},
            limit=HISTORY_LIMIT,
            sort=[("created_at", 1)],
        )
        await websocket.send_json({"type": "history", "data": history})
    except Exception:
        await websocket.send_json({"type": "history", "data": []})

    online = store_manager.online_users(mall_id)

    # 欢迎当前用户并告知在线列表
    await websocket.send_json({
        "type": "system",
        "content": "成功加入店铺聊天室",
        "username": username,
        "online_users": online,
        "created_at": now_str,
    })

    # 向其他成员广播新成员加入
    await store_manager.broadcast(mall_id, {
        "type": "system",
        "content": f"{username} 加入了聊天",
        "username": username,
        "online_users": online,
        "created_at": now_str,
    }, exclude=username)

    # ── 消息循环 ──────────────────────────────────────────────────────────────
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
            if not content:
                continue

            ts = datetime.datetime.now().isoformat(timespec="seconds")

            # 持久化到 MongoDB
            try:
                await mongodb.insert_one(COLLECTION, {
                    "mall_id": mall_id,
                    "username": username,
                    "content": content,
                    "created_at": ts,
                })
            except Exception:
                pass

            # 广播给店铺内所有连接（含发送者自身，用于前端回显确认）
            await store_manager.broadcast(mall_id, {
                "type": "chat",
                "username": username,
                "content": content,
                "created_at": ts,
            })

    except WebSocketDisconnect:
        store_manager.disconnect(mall_id, username)
        await store_manager.broadcast(mall_id, {
            "type": "system",
            "content": f"{username} 离开了聊天",
            "username": username,
            "online_users": store_manager.online_users(mall_id),
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        })
