import logging
from datetime import datetime, timezone
from typing import Optional

from data.mongodb_client import MongoDBClient
from data.redis_client import RedisClient
from services.cache_service import CacheService

_logger = logging.getLogger("fastapi_logger")



class Record:
    """
    用户行为记录服务（与 recommend 模型训练数据对齐）

    当前推荐模型主要使用 user_browse_record 集合中的:
    - user
    - shopping_id（兼容保留 commodity_id）
    - count
    """

    COLLECTION_NAME = "user_browse_record"
    _ACTION_WEIGHT = {
        "browse": 1.0,
        "buy": 3.0,
    }

    def __init__(
        self,
        mongodb: MongoDBClient,
        redis_client: Optional[RedisClient] = None,
        record_cache_ttl: int = 300,
    ):
        self.mongodb = mongodb
        self.cache = CacheService(redis_client) if redis_client else None
        self.record_cache_ttl = max(30, int(record_cache_ttl))

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _safe_user(user: str) -> str:
        return (user or "").strip()

    @staticmethod
    def _safe_int(value: int) -> int:
        return int(value)

    def _record_cache_key(self, user: str, limit: int) -> str:
        return f"record:user:{user}:limit:{limit}"

    def _record_cache_pattern(self, user: str) -> str:
        return f"record:user:{user}:*"

    def _recommend_cache_pattern(self, user: str) -> str:
        return f"recommend_commodity_list:user:{user}:*"

    async def _invalidate_related_cache(self, user: str) -> None:
        """
        行为变化后失效相关缓存：
        1) 用户行为记录缓存
        2) 基于用户行为的推荐结果缓存
        """
        if self.cache is None:
            return
        try:
            await self.cache.delete_pattern(self._record_cache_pattern(user))
            await self.cache.delete_pattern(self._recommend_cache_pattern(user))
        except Exception:
            # 缓存失效异常不影响主流程
            pass

    async def init_indexes(self) -> bool:
        """初始化记录集合索引，避免重复并提高查询性能。"""
        try:
            await self.mongodb.create_index(
                self.COLLECTION_NAME,
                [("user", 1), ("shopping_id", 1)],
                unique=True,
            )
            await self.mongodb.create_index(
                self.COLLECTION_NAME,
                [("user", 1), ("updated_at", -1)],
                unique=False,
            )
            return True
        except Exception:
            return False

    async def _upsert_action(
        self,
        user: str,
        shopping_id: int,
        mall_id: int,
        action: str,
    ) -> bool:
        user = self._safe_user(user)
        if not user:
            return False

        sid = self._safe_int(shopping_id)
        mid = self._safe_int(mall_id)
        now = self._now_iso()
        weight = self._ACTION_WEIGHT.get(action, 1.0)
        action_count_field = "browse_count" if action == "browse" else "buy_count"

        query = {"user": user, "shopping_id": sid}
        update = {
            "$set": {
                "mall_id": mid,
                "commodity_id": sid,  # 兼容历史字段
                "last_action": action,
                "updated_at": now,
            },
            "$setOnInsert": {
                "user": user,
                "shopping_id": sid,
                "created_at": now,
            },
            "$inc": {
                "count": 1,
                action_count_field: 1,
                "score": weight,
            },
        }

        try:
            await self.mongodb.update_one(self.COLLECTION_NAME, query, update, upsert=True)
            await self._invalidate_related_cache(user)
            return True
        except Exception as e:
            _logger.error(f"[Record._upsert_action] MongoDB写入失败 user={user} shopping_id={sid} action={action} error={type(e).__name__}: {e}")
            return False

    async def browse_record(self, user: str, shopping_id: int, mall_id: int) -> bool:
        """记录浏览行为（推荐训练的主数据来源）。"""
        return await self._upsert_action(user, shopping_id, mall_id, action="browse")

    async def buy_record(self, user: str, shopping_id: int, mall_id: int) -> bool:
        """记录购买行为（用于提升后续推荐权重）。"""
        return await self._upsert_action(user, shopping_id, mall_id, action="buy")

    async def get_user_records(
        self,
        user: str,
        limit: int = 100,
    ) -> list[dict]:
        """获取用户最近行为记录，便于推荐调试或画像分析。"""
        user = self._safe_user(user)
        if not user:
            return []
        safe_limit = max(1, int(limit))
        cache_key = self._record_cache_key(user, safe_limit)

        if self.cache is not None:
            try:
                cached = await self.cache.get(cache_key)
                if cached is not None:
                    return cached
            except Exception:
                pass

        result = await self.mongodb.find_many(
            self.COLLECTION_NAME,
            {"user": user},
            limit=safe_limit,
            sort=[("updated_at", -1)],
        )

        if self.cache is not None:
            try:
                await self.cache.set(cache_key, result, expire=self.record_cache_ttl)
            except Exception:
                pass

        return result

    async def clear_user_cache(self, user: str) -> bool:
        """手动清理某用户行为与推荐缓存。"""
        user = self._safe_user(user)
        if not user or self.cache is None:
            return False
        try:
            await self._invalidate_related_cache(user)
            return True
        except Exception:
            return False