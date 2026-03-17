from typing import Optional

import jwt

from config.jwt_config import jwt_settings
from data.redis_client import RedisClient
from data.sql_client_pool import db_pool
from services.verify_duter_token import VerifyDuterToken


class CustomerServiceAuth:
    """
    在线客服接入鉴权。

    - client_type='user'   → 普通用户 JWT（JWT_USER_SECRET_KEY），无需绑定店铺
    - client_type='seller' → 商户端 JWT（JWT_SELLER_SECRET_KEY），需验证对目标店铺的管理权
    """

    def __init__(self, token: str, client_type: str, redis: RedisClient):
        self._token = token
        self._client_type = client_type
        self._redis = redis

    async def authenticate(self, mall_id: int) -> Optional[str]:
        """
        统一鉴权入口。

        :param mall_id: 目标店铺 ID
        :return: 验证通过时返回用户名，否则返回 None
        """
        if self._client_type == "user":
            return await self._verify_user()
        elif self._client_type == "seller":
            return await self._verify_seller(mall_id)
        return None

    async def _verify_user(self) -> Optional[str]:
        """普通用户 JWT 验证（仅解析，不绑定店铺）。"""
        try:
            parts = self._token.split(" ")
            raw_token = parts[1] if len(parts) == 2 else parts[0]
            payload: dict = jwt.decode(
                raw_token, jwt_settings.JWT_USER_SECRET_KEY, algorithms=["HS256"]
            )
            user = payload.get("user")
            return user if user else None
        except Exception:
            return None

    async def _verify_seller(self, mall_id: int) -> Optional[str]:
        """商户端 JWT 验证（复用 StoreChatAuth 相同逻辑）。"""
        verifier = VerifyDuterToken(self._token, self._redis)
        token_data = await verifier.token_data()
        if not token_data:
            return None

        station = token_data.get("station")
        if station == "1":
            return await self._verify_main_merchant(verifier, token_data, mall_id)
        elif station == "2":
            return await self._verify_store_user(verifier, token_data, mall_id)
        return None

    async def _verify_main_merchant(
        self, verifier: VerifyDuterToken, token_data: dict, mall_id: int
    ) -> Optional[str]:
        state_id_list: list = token_data.get("state_id_list") or []
        if mall_id not in state_id_list:
            return None
        username = token_data.get("user")
        sql_data = await db_pool.execute_query(
            "SELECT user FROM seller_sing WHERE user = %s", (username,)
        )
        result = await verifier.verify_token(sql_data)
        return username if (result and result[0]) else None

    async def _verify_store_user(
        self, verifier: VerifyDuterToken, token_data: dict, mall_id: int
    ) -> Optional[str]:
        if token_data.get("mall_id") != mall_id:
            return None
        username = token_data.get("user")
        sql_data = await db_pool.execute_query(
            "SELECT user FROM store_user WHERE user = %s AND store_id = %s",
            (username, mall_id),
        )
        result = await verifier.verify_token(sql_data)
        return username if (result and result[0]) else None
