from typing import Optional

from data.redis_client import RedisClient
from data.sql_client_pool import db_pool
from services.verify_duter_token import VerifyDuterToken


class StoreChatAuth:
    """
    店铺聊天室访问鉴权服务。

    复用 VerifyDuterToken 完成 JWT 解析 + Redis 过期时间验证，
    并在此基础上追加"是否有权访问目标店铺"的业务校验。

    用法示例：
        auth = StoreChatAuth(token, redis)
        username = await auth.authenticate(mall_id)
        if username is None:
            # 鉴权失败
    """

    def __init__(self, token: str, redis: RedisClient):
        """
        :param token: 商户端 JWT Token（格式同其他卖家端接口，可带 bearer 前缀）
        :param redis: Redis 客户端实例
        """
        self._verifier = VerifyDuterToken(token, redis)

    async def authenticate(self, mall_id: int) -> Optional[str]:
        """
        统一鉴权入口。

        :param mall_id: 目标店铺 ID
        :return: 验证通过时返回用户名，否则返回 None
        """
        token_data = await self._verifier.token_data()
        if not token_data:
            return None

        station = token_data.get("station")
        if station == "1":
            return await self._verify_main_merchant(token_data, mall_id)
        elif station == "2":
            return await self._verify_store_user(token_data, mall_id)
        return None

    async def _verify_main_merchant(self, token_data: dict, mall_id: int) -> Optional[str]:
        """
        主商户（station='1'）校验：
        1. 目标 mall_id 必须在 token 内的 state_id_list 中
        2. 通过 VerifyDuterToken.verify_token 验证 Redis 过期时间戳
        """
        state_id_list: list = token_data.get("state_id_list") or []
        if mall_id not in state_id_list:
            return None

        username = token_data.get("user")
        sql_data = await db_pool.execute_query(
            "SELECT user FROM seller_sing WHERE user = %s", (username,)
        )
        result = await self._verifier.verify_token(sql_data)
        return username if (result and result[0]) else None

    async def _verify_store_user(self, token_data: dict, mall_id: int) -> Optional[str]:
        """
        店铺员工（station='2'）校验：
        1. token 内绑定的 mall_id 必须与目标一致
        2. 通过 VerifyDuterToken.verify_token 验证 Redis 过期时间戳
        """
        if token_data.get("mall_id") != mall_id:
            return None

        username = token_data.get("user")
        sql_data = await db_pool.execute_query(
            "SELECT user FROM store_user WHERE user = %s AND store_id = %s",
            (username, mall_id),
        )
        result = await self._verifier.verify_token(sql_data)
        return username if (result and result[0]) else None
