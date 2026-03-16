from typing import Dict, List
from fastapi import WebSocket


class StoreConnectionManager:
    """
    店铺内员工 WebSocket 连接管理器。

    按 mall_id 隔离每个店铺的连接池，提供：
    - 连接 / 断开
    - 店铺内全员广播
    - 获取在线用户列表
    """

    def __init__(self):
        self._rooms: Dict[int, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, mall_id: int, username: str) -> None:
        """接受 WebSocket 握手并注册连接。"""
        await websocket.accept()
        self._rooms.setdefault(mall_id, {})[username] = websocket

    def disconnect(self, mall_id: int, username: str) -> None:
        """移除连接；若该店铺已无连接则清理房间。"""
        room = self._rooms.get(mall_id, {})
        room.pop(username, None)
        if not room:
            self._rooms.pop(mall_id, None)

    async def broadcast(
        self,
        mall_id: int,
        message: dict,
        exclude: str | None = None,
    ) -> None:
        """向指定店铺的所有连接广播消息，可排除某个用户。"""
        for uname, ws in list(self._rooms.get(mall_id, {}).items()):
            if uname == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                pass

    def online_users(self, mall_id: int) -> List[str]:
        """返回指定店铺当前在线的用户名列表。"""
        return list(self._rooms.get(mall_id, {}).keys())


# 全局单例，供路由层直接导入使用
store_manager = StoreConnectionManager()
