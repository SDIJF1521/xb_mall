from data.redis_client import RedisClient
from ..user_info import UserInfo
import time
import asyncio
from typing import Dict, Any, Optional

class OnLine:
    def __init__(self, redis_client: RedisClient, token: Optional[str] = None, detection_time: int = 60):
        """
        初始化在线状态管理类
        
        Args:
            redis_client: Redis客户端实例
            token: 用户令牌
            detection_time: 心跳检测过期时间（秒）
        """
        self.redis_client = redis_client
        self.token = token
        self.detection_time = detection_time
        self.user_data = {"current": False, "msg": "未登录"}
        self.user_id = None
        self._init_complete = asyncio.Event()
        
        if token:
            self._init_task = asyncio.create_task(self._init_user_data())
        
        # 启动定期清理任务
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _init_user_data(self):
        """
        异步初始化用户数据
        """
        try:
            user = UserInfo(self.token)
            self.user_data = await user.token_analysis()
            if self.user_data["current"]:
                self.user_id = self.user_data["user"]
        finally:
            self._init_complete.set()
    
    async def wait_init(self):
        await self._init_complete.wait()
        return self.user_data["current"]


    async def up_line(self) -> Dict[str, Any]:
        """用户上线"""
        if not self.user_id:
            return {"msg": self.user_data.get("msg", "请先登录"), "current": False}
            
        # 检查用户是否已在线
        online_state = await self.on_line_state()
        if online_state["current"]:
            return {"msg": "用户已在线", "current": True}
            
        try:
            # 记录上线时间（整数时间戳更规范）
            timestamp = int(time.time())
            await self.redis_client.hset("online", self.user_id, str(timestamp))
            # 设置心跳过期时间（用于异常离线检测）
            await self.redis_client.setex(f"online:{self.user_id}", self.detection_time, "1")
            return {"msg": "上线成功", "current": True}
        except Exception as e:
            return {"msg": f"上线失败: {str(e)}", "current": False}

    async def on_line_state(self) -> Dict[str, Any]:
        """检测用户在线状态"""
        if not self.user_id:
            return self.user_data
            
        try:
            online_status = await self.redis_client.hget("online", self.user_id)
            if online_status:
                await self.redis_client.expire(f"online:{self.user_id}", self.detection_time)
                return {"msg": "用户在线", "current": True}
            return {"msg": "用户离线", "current": False}
        except Exception as e:
            return {"msg": f"状态检测失败: {str(e)}", "current": False}

    async def on_line_heartbeat(self) -> Dict[str, Any]:
        """用户心跳检测"""
        if not self.user_id:
            return self.user_data
            
        try:
            # 检查是否存在心跳标记（防异常离线）
            heartbeat_key = f"online:{self.user_id}"

            heartbeat_exists = await self.redis_client.get(heartbeat_key)
            
            if not heartbeat_exists:
                await self.up_line()
                return {"msg": "用户已离线（心跳过期）", "current": False}
                
            # 更新在线时间
            timestamp = int(time.time())
            await self.redis_client.hset("online", self.user_id, str(timestamp))
            # 重置心跳过期时间
            await self.redis_client.setex(heartbeat_key, self.detection_time, "1")
            return {"msg": "心跳检测成功，用户在线", "current": True}
        except Exception as e:
            return {"msg": f"心跳检测失败: {str(e)}", "current": False}

    async def off_line(self) -> Dict[str, Any]:
        """用户下线"""
        if not self.user_id:
            return self.user_data
            
        try:
            # 删除在线记录和心跳标记
            await asyncio.gather(
                self.redis_client.hdel("online", self.user_id),
                self.redis_client.delete(f"online:{self.user_id}")
            )
            return {"msg": "下线成功", "current": True}
        except Exception as e:
            return {"msg": f"下线失败: {str(e)}", "current": False}

    async def get_online_users(self) -> Dict[str, Any]:
        """获取在线用户列表"""
        try:
            online_users = await self.redis_client.hgetall("online")
            if online_users:
                # 转换时间戳为可读格式（可选）
                formatted_users = {
                    user: f"{time.ctime(float(timestamp))} ({timestamp})"
                    for user, timestamp in online_users.items()
                }
                return {"online_users": formatted_users, "current": True}
            return {"msg": "没有在线用户", "current": False}
        except Exception as e:
            return {"msg": f"获取在线用户失败: {str(e)}", "current": False}

    async def _periodic_cleanup(self):
        """定期清理过期用户"""
        while True:
            await asyncio.sleep(self.detection_time)
            await self._cleanup_expired_users()
    
    async def _cleanup_expired_users(self):
        """清理心跳已过期的用户"""
        cursor = 0
        try:
            while True:
                # 分批扫描哈希表以避免阻塞Redis
                cursor, user_entries = await self.redis_client.hscan("online", cursor, count=100)
                for user_id_bytes in user_entries:
                    user_id = user_id_bytes
                    heartbeat_key = f"online:{user_id}"
                    # 检查心跳键是否存在
                    heartbeat_exists = await self.redis_client.get(heartbeat_key)
                    if not heartbeat_exists:
                         # 删除在线记录和心跳标记
                        await asyncio.gather(
                            self.redis_client.hdel("online",  user_id),
                            self.redis_client.delete(f"online:{user_id}")
                        )
                if cursor == 0:
                    break
        except Exception as e:
            # 生产环境中应使用 proper logging 替代 print
            print(f"清理过期用户时出错: {str(e)}")