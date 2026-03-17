from typing import Dict, List, Optional
from fastapi import WebSocket


class CustomerServiceManager:
    """
    在线客服 WebSocket 连接管理器。

    按 mall_id 隔离每个店铺的连接池：
    - users:   普通用户连接，key 为用户名（session_id）
    - sellers: 卖家端连接，key 为卖家用户名（一个店铺可多个客服在线）
    """

    def __init__(self):
        # {mall_id: {"users": {username: WebSocket}, "sellers": {username: WebSocket}}}
        self._rooms: Dict[int, Dict[str, Dict[str, WebSocket]]] = {}

    def _get_room(self, mall_id: int) -> Dict[str, Dict[str, WebSocket]]:
        if mall_id not in self._rooms:
            self._rooms[mall_id] = {"users": {}, "sellers": {}}
        return self._rooms[mall_id]

    # ── 连接 / 断开 ────────────────────────────────────────────────────────────

    async def connect_user(self, websocket: WebSocket, mall_id: int, username: str) -> None:
        await websocket.accept()
        self._get_room(mall_id)["users"][username] = websocket

    async def connect_seller(self, websocket: WebSocket, mall_id: int, username: str) -> None:
        await websocket.accept()
        self._get_room(mall_id)["sellers"][username] = websocket

    def disconnect_user(self, mall_id: int, username: str) -> None:
        room = self._rooms.get(mall_id)
        if room:
            room["users"].pop(username, None)
            if not room["users"] and not room["sellers"]:
                self._rooms.pop(mall_id, None)

    def disconnect_seller(self, mall_id: int, username: str) -> None:
        room = self._rooms.get(mall_id)
        if room:
            room["sellers"].pop(username, None)
            if not room["users"] and not room["sellers"]:
                self._rooms.pop(mall_id, None)

    # ── 发送 ───────────────────────────────────────────────────────────────────

    async def send_to_user(self, mall_id: int, username: str, message: dict) -> bool:
        """向指定用户发送消息，连接不存在时返回 False。"""
        ws = self._rooms.get(mall_id, {}).get("users", {}).get(username)
        if ws:
            try:
                await ws.send_json(message)
                return True
            except Exception:
                pass
        return False

    async def broadcast_to_sellers(self, mall_id: int, message: dict) -> None:
        """向该店铺所有在线卖家广播消息。"""
        for ws in list(self._rooms.get(mall_id, {}).get("sellers", {}).values()):
            try:
                await ws.send_json(message)
            except Exception:
                pass

    # ── 状态查询 ──────────────────────────────────────────────────────────────

    def online_users(self, mall_id: int) -> List[str]:
        return list(self._rooms.get(mall_id, {}).get("users", {}).keys())

    def is_user_online(self, mall_id: int, username: str) -> bool:
        return username in self._rooms.get(mall_id, {}).get("users", {})

    def has_sellers_online(self, mall_id: int) -> bool:
        return bool(self._rooms.get(mall_id, {}).get("sellers"))


# 全局单例
cs_manager = CustomerServiceManager()
