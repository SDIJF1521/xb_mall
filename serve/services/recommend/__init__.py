"""
AI商品推荐服务
优先使用 Wide & Deep 深度学习模型 (Google, 2016)
- Wide: 线性 + 交叉特征, 记忆历史共现
- Deep: 嵌入 + MLP, 泛化到未见组合
数据来源: user_browse_record, shopping, user_favorites
"""
import logging
from pathlib import Path
from typing import List

from data.mongodb_client import MongoDBClient
from data.sql_client_pool import db_pool

# Wide & Deep 模型目录
WIDE_DEEP_MODEL_DIR = Path(__file__).resolve().parent / "models" / "wide_deep"
logger = logging.getLogger("fastapi_logger")


class RecommendCommodity:
    """基于 Wide & Deep 的商品推荐服务"""

    _wide_deep = None
    _wd_loaded = False
    _artifact_signature = None

    def __init__(self, mongodb: MongoDBClient):
        self.mongodb = mongodb

    @classmethod
    def _get_artifact_signature(cls):
        paths = [
            WIDE_DEEP_MODEL_DIR / "config.json",
            WIDE_DEEP_MODEL_DIR / "model.pt",
            WIDE_DEEP_MODEL_DIR / "vocab.json",
            WIDE_DEEP_MODEL_DIR / "training_state.json",
        ]
        if not all(path.exists() for path in paths[:3]):
            return None
        return tuple(path.stat().st_mtime_ns if path.exists() else 0 for path in paths)

    @classmethod
    def force_reload(cls):
        cls._wide_deep = None
        cls._wd_loaded = False
        cls._artifact_signature = None

    # 获取 Wide & Deep 模型
    def _get_wide_deep(self):
        """懒加载 Wide & Deep 模型"""
        artifact_signature = self._get_artifact_signature()
        if artifact_signature != self.__class__._artifact_signature:
            self.__class__.force_reload()
            self.__class__._artifact_signature = artifact_signature

        if self.__class__._wd_loaded:
            return self.__class__._wide_deep
        try:
            from services.recommend.wide_deep import WideDeepRecommender

            rec = WideDeepRecommender(model_dir=WIDE_DEEP_MODEL_DIR)
            if rec.load():
                self.__class__._wide_deep = rec
        except Exception as exc:
            logger.warning(f"加载 Wide & Deep 模型失败: {exc}")
        self.__class__._wd_loaded = True
        return self.__class__._wide_deep

    async def _load_user_favorites(self, user: str) -> set[int]:
        """从 MySQL 加载用户收藏的商品ID集合"""
        try:
            rows = await db_pool.execute_query(
                "SELECT shopping_id FROM user_favorites "
                "WHERE user = %s AND type = 'commodity' AND shopping_id IS NOT NULL",
                (user,),
            )
            return {int(r[0]) for r in rows} if rows else set()
        except Exception:
            return set()

    async def _load_user_fav_types(self, user: str) -> list[str]:
        """获取用户收藏商品所属的类型列表，用于类型偏好加权"""
        fav_ids = await self._load_user_favorites(user)
        types: list[str] = []
        for sid in fav_ids:
            prod = await self.mongodb.find_one("shopping", {"shopping_id": sid})
            if prod:
                t = prod.get("type") or []
                if isinstance(t, str):
                    t = [t]
                types.extend(str(x) for x in t if x)
        return types

    # 基于 Wide & Deep 的智能推荐
    async def _index_recommend_commodity(self, user: str) -> List[int]:
        """
        基于 Wide & Deep 的智能推荐，同时融合收藏偏好加权
        :param user: 用户名
        :return: 推荐的 shopping_id 列表(最多12个)
        """
        wd = self._get_wide_deep()
        if wd is None:
            return await self._fallback_collaborative_filter(user)

        # 获取已审核候选商品
        audit_rows = await db_pool.execute_query(
            "SELECT s.shopping_id "
            "FROM shopping s "
            "JOIN store st ON s.mall_id = st.mall_id "
            "WHERE s.audit = 1 AND st.state = 1"
        )
        if not audit_rows:
            return []
        candidate_ids = [int(r[0]) for r in audit_rows]

        # 获取用户浏览历史和收藏历史
        user_records = await self.mongodb.find_many("user_browse_record", {"user": user})
        interacted = set()
        for r in user_records:
            sid = r.get("shopping_id") or r.get("commodity_id")
            if sid is not None:
                interacted.add(int(sid))

        fav_ids = await self._load_user_favorites(user)

        candidates = [i for i in candidate_ids if i not in interacted]
        if not candidates:
            return []

        # 构建商品特征 (item_id -> (item_idx, type_idx, price_norm))
        import math
        item_feats: dict[int, tuple[int, int, float]] = {}
        type2idx = getattr(wd, "type2idx", {})
        item2idx = getattr(wd, "item2idx", {})

        for iid in candidates:
            prod = await self.mongodb.find_one("shopping", {"shopping_id": iid})
            if not prod:
                continue
            types = prod.get("type") or []
            if isinstance(types, str):
                types = [types]
            type_str = str(types[0]) if types else "<pad>"
            tidx = type2idx.get(type_str, 0)
            spec_list = prod.get("specification_list") or []
            price = float(spec_list[0].get("price", 0)) if spec_list else 0.0
            idx = item2idx.get(iid, 0)
            pnorm = math.log1p(price) / 10.0 if price > 0 else 0.0
            item_feats[iid] = (idx, tidx, min(pnorm, 1.0))

        if not item_feats:
            return []

        ids = wd.recommend(user, list(item_feats.keys()), item_feats, top_k=24)
        if not ids:
            return await self._fallback_collaborative_filter(user)

        # 收藏类型偏好加权：与收藏商品同类型的候选商品获得排序提升
        fav_types = await self._load_user_fav_types(user)
        if fav_types:
            from collections import Counter
            type_freq = Counter(fav_types)
            scored: list[tuple[int, float]] = []
            for rank, sid in enumerate(ids):
                base_score = 1.0 / (rank + 1)
                prod = await self.mongodb.find_one("shopping", {"shopping_id": sid})
                bonus = 0.0
                if prod:
                    ptypes = prod.get("type") or []
                    if isinstance(ptypes, str):
                        ptypes = [ptypes]
                    for t in ptypes:
                        bonus += type_freq.get(str(t), 0) * 0.15
                scored.append((sid, base_score + bonus))
            scored.sort(key=lambda x: -x[1])
            return [s for s, _ in scored[:12]]

        return ids[:12]

    # 无 Wide & Deep 模型时, 使用协同过滤回退
    async def _fallback_collaborative_filter(self, user: str) -> List[int]:
        """无 Wide & Deep 模型时, 使用协同过滤 + 收藏偏好回退"""
        from collections import defaultdict

        def _get_sid(r):
            return r.get("shopping_id") or r.get("commodity_id")

        user_records = await self.mongodb.find_many("user_browse_record", {"user": user})
        fav_ids = await self._load_user_favorites(user)

        user_item_ids = {
            int(_get_sid(r)) for r in user_records
            if _get_sid(r) is not None
        }
        user_item_ids |= fav_ids

        if not user_item_ids:
            return []

        all_records = await self.mongodb.find_many("user_browse_record", {})
        if not all_records:
            return []

        user_items: dict = defaultdict(set)
        for r in all_records:
            u, sid = r.get("user"), _get_sid(r)
            if u and sid is not None:
                user_items[u].add(int(sid))

        item_scores: dict[int, float] = defaultdict(float)
        for ou, oi in user_items.items():
            if ou == user:
                continue
            overlap = user_item_ids & oi
            if not overlap:
                continue
            for item in oi - user_item_ids:
                item_scores[item] += len(overlap)

        type_scores: dict[int, float] = defaultdict(float)
        source_ids = user_item_ids.copy()
        for sid in source_ids:
            prod = await self.mongodb.find_one("shopping", {"shopping_id": sid})
            if prod and prod.get("type"):
                types = prod["type"] if isinstance(prod["type"], list) else [prod["type"]]
                weight = 2.0 if sid in fav_ids else 1.0
                for t in types:
                    t_val = str(t) if t else "<pad>"
                    similar = await self.mongodb.find_many(
                        "shopping", {"type": t_val}, limit=50
                    )
                    for s in similar:
                        sid2 = s.get("shopping_id")
                        if sid2 is not None and int(sid2) not in user_item_ids:
                            type_scores[int(sid2)] += weight

        for item in set(item_scores) | set(type_scores):
            item_scores[item] = item_scores.get(item, 0) * 0.6 + type_scores.get(item, 0) * 0.4

        audit_rows = await db_pool.execute_query(
            "SELECT s.shopping_id "
            "FROM shopping s "
            "JOIN store st ON s.mall_id = st.mall_id "
            "WHERE s.audit = 1 AND st.state = 1"
        )
        if not audit_rows:
            return []
        audited = {int(r[0]) for r in audit_rows}
        candidates = [(s, sc) for s, sc in item_scores.items() if s in audited]
        candidates.sort(key=lambda x: -x[1])
        return [s for s, _ in candidates[:12]]
