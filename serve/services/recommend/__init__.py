"""
AI商品推荐服务
优先使用 Wide & Deep 深度学习模型 (Google, 2016)
- Wide: 线性 + 交叉特征, 记忆历史共现
- Deep: 嵌入 + MLP, 泛化到未见组合
数据来源: user_browse_record, shopping
"""
from pathlib import Path
from typing import List

from data.mongodb_client import MongoDBClient
from data.sql_client_pool import db_pool

# Wide & Deep 模型目录
WIDE_DEEP_MODEL_DIR = Path(__file__).resolve().parent / "models" / "wide_deep"


class RecommendCommodity:
    """基于 Wide & Deep 的商品推荐服务"""

    def __init__(self, mongodb: MongoDBClient):
        self.mongodb = mongodb
        self._wide_deep = None
        self._wd_loaded = False

    def _get_wide_deep(self):
        """懒加载 Wide & Deep 模型"""
        if self._wd_loaded:
            return self._wide_deep
        try:
            from services.recommend.wide_deep import WideDeepRecommender
            rec = WideDeepRecommender(model_dir=WIDE_DEEP_MODEL_DIR)
            if rec.load():
                self._wide_deep = rec
        except Exception:
            pass
        self._wd_loaded = True
        return self._wide_deep

    async def _index_recommend_commodity(self, user: str) -> List[int]:
        """
        基于 Wide & Deep 的智能推荐
        :param user: 用户名
        :return: 推荐的 shopping_id 列表(最多12个)
        """
        wd = self._get_wide_deep()
        if wd is None:
            return await self._fallback_collaborative_filter(user)

        # 获取已审核候选商品
        audit_rows = await db_pool.execute_query(
            "SELECT shopping_id FROM shopping WHERE audit = 1"
        )
        if not audit_rows:
            return []
        candidate_ids = [int(r[0]) for r in audit_rows]

        # 获取用户历史, 排除已交互商品
        user_records = await self.mongodb.find_many("user_browse_record", {"user": user})
        interacted = set()
        for r in user_records:
            sid = r.get("shopping_id") or r.get("commodity_id")
            if sid is not None:
                interacted.add(int(sid))

        candidates = [i for i in candidate_ids if i not in interacted]
        if not candidates:
            return []

        # 构建商品特征 (item_id -> (item_idx, type_idx, price_norm))
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
            # 简单归一化
            import math
            pnorm = math.log1p(price) / 10.0 if price > 0 else 0.0
            item_feats[iid] = (idx, tidx, min(pnorm, 1.0))

        if not item_feats:
            return []

        ids = wd.recommend(user, list(item_feats.keys()), item_feats, top_k=12)
        if ids:
            return ids
        return await self._fallback_collaborative_filter(user)

    async def _fallback_collaborative_filter(self, user: str) -> List[int]:
        """无 Wide & Deep 模型时, 使用协同过滤回退"""
        from collections import defaultdict

        def _get_sid(r):
            return r.get("shopping_id") or r.get("commodity_id")

        user_records = await self.mongodb.find_many("user_browse_record", {"user": user})
        if not user_records:
            return []

        user_item_ids = {
            int(_get_sid(r)) for r in user_records
            if _get_sid(r) is not None
        }
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
        for sid in user_item_ids:
            prod = await self.mongodb.find_one("shopping", {"shopping_id": sid})
            if prod and prod.get("type"):
                types = prod["type"] if isinstance(prod["type"], list) else [prod["type"]]
                for t in types:
                    t_val = str(t) if t else "<pad>"
                    similar = await self.mongodb.find_many(
                        "shopping", {"type": t_val}, limit=50
                    )
                    for s in similar:
                        sid2 = s.get("shopping_id")
                        if sid2 is not None and int(sid2) not in user_item_ids:
                            type_scores[int(sid2)] += 1.0

        for item in set(item_scores) | set(type_scores):
            item_scores[item] = item_scores.get(item, 0) * 0.6 + type_scores.get(item, 0) * 0.4

        audit_rows = await db_pool.execute_query(
            "SELECT shopping_id FROM shopping WHERE audit = 1"
        )
        if not audit_rows:
            return []
        audited = {int(r[0]) for r in audit_rows}
        candidates = [(s, sc) for s, sc in item_scores.items() if s in audited]
        candidates.sort(key=lambda x: -x[1])
        return [s for s, _ in candidates[:12]]
