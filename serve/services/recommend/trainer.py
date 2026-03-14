import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from data.mongodb_client import MongoDBClient
from data.redis_client import RedisClient
from services.cache_service import CacheService
from services.recommend import WIDE_DEEP_MODEL_DIR
from services.recommend.wide_deep.dataset import (
    build_vocab,
    detect_vocab_changes,
    filter_records_after,
    get_latest_record_timestamp,
    load_vocab,
    summarize_vocab,
)
from services.recommend.wide_deep.train import (
    incremental_train_from_data,
    train_full_from_data,
)

logger = logging.getLogger("fastapi_logger")


class RecommendTrainer:
    """统一管理推荐模型的全量训练、增量训练和训练状态。"""

    STATE_FILE_NAME = "training_state.json"

    def __init__(
        self,
        mongodb: MongoDBClient,
        redis_client: RedisClient | None = None,
        model_dir: str | Path = WIDE_DEEP_MODEL_DIR,
    ):
        self.mongodb = mongodb
        self.redis_client = redis_client
        self.model_dir = Path(model_dir)
        self.state_path = self.model_dir / self.STATE_FILE_NAME

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning(f"读取推荐训练状态失败: {exc}")
            return {}

    def save_state(self, state: dict[str, Any]) -> None:
        self.model_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=self.model_dir, encoding="utf-8", suffix=".tmp"
        ) as tmp:
            json.dump(state, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, self.state_path)

    async def _load_training_data(self) -> tuple[list[dict], list[dict]]:
        user_records = await self.mongodb.find_many("user_browse_record", {})
        shopping_items = await self.mongodb.find_many("shopping", {})
        return user_records, shopping_items

    async def _invalidate_recommend_cache(self) -> None:
        if self.redis_client is None:
            return
        try:
            cache = CacheService(self.redis_client)
            await cache.delete_pattern("recommend_commodity_list:user:*")
        except Exception as exc:
            logger.warning(f"清理推荐缓存失败: {exc}")

    def _artifacts_exist(self) -> bool:
        required = ("config.json", "model.pt", "vocab.json")
        return all((self.model_dir / file_name).exists() for file_name in required)

    async def run_scheduled_training(
        self,
        full_epochs: int = 10,
        incremental_epochs: int = 3,
        batch_size: int = 256,
        full_lr: float = 0.001,
        incremental_lr: float = 0.0005,
        negative_ratio: int = 4,
    ) -> dict[str, Any]:
        user_records, shopping_items = await self._load_training_data()
        latest_record_at = get_latest_record_timestamp(user_records)
        state = self.load_state()

        if not user_records or not shopping_items:
            return {
                "status": "skipped",
                "reason": "insufficient_data",
                "latest_record_at": latest_record_at,
            }

        if not self._artifacts_exist():
            result = train_full_from_data(
                user_records,
                shopping_items,
                model_dir=self.model_dir,
                epochs=full_epochs,
                batch_size=batch_size,
                lr=full_lr,
                negative_ratio=negative_ratio,
            )
            vocab = build_vocab(user_records, shopping_items)
            new_state = {
                "last_trained_at": latest_record_at,
                "last_training_mode": "full",
                "last_training_samples": result["samples"],
                "vocab_summary": summarize_vocab(*vocab),
            }
            self.save_state(new_state)
            await self._invalidate_recommend_cache()
            return {"status": "trained", **new_state}

        new_records = filter_records_after(user_records, state.get("last_trained_at"))
        if not new_records:
            return {
                "status": "skipped",
                "reason": "no_new_records",
                "last_trained_at": state.get("last_trained_at"),
                "latest_record_at": latest_record_at,
            }

        user2idx, item2idx, type2idx = load_vocab(str(self.model_dir / "vocab.json"))
        vocab_changes = detect_vocab_changes(
            user_records,
            shopping_items,
            user2idx,
            item2idx,
            type2idx,
        )

        if vocab_changes["requires_full_rebuild"]:
            result = train_full_from_data(
                user_records,
                shopping_items,
                model_dir=self.model_dir,
                epochs=full_epochs,
                batch_size=batch_size,
                lr=full_lr,
                negative_ratio=negative_ratio,
            )
            vocab = build_vocab(user_records, shopping_items)
            training_mode = "full"
            vocab_summary = summarize_vocab(*vocab)
        else:
            result = incremental_train_from_data(
                new_records,
                shopping_items,
                model_dir=self.model_dir,
                epochs=incremental_epochs,
                batch_size=batch_size,
                lr=incremental_lr,
                negative_ratio=negative_ratio,
            )
            training_mode = "incremental"
            vocab_summary = summarize_vocab(user2idx, item2idx, type2idx)

        new_state = {
            "last_trained_at": latest_record_at,
            "last_training_mode": training_mode,
            "last_training_samples": result["samples"],
            "vocab_summary": vocab_summary,
            "vocab_change_flags": vocab_changes,
        }
        self.save_state(new_state)
        await self._invalidate_recommend_cache()
        return {"status": "trained", **new_state}
