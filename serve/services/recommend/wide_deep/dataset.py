"""
Wide & Deep 数据准备
从 user_browse_record 和 shopping 构建训练样本
"""
import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# 获取商品ID
def _get_shopping_id(r: dict) -> int | None:
    sid = r.get("shopping_id") or r.get("commodity_id")
    return int(sid) if sid is not None else None

# 解析ISO时间
def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None

# 构建词表
def build_vocab(
    user_records: List[dict],
    shopping_items: List[dict],
) -> Tuple[Dict[str, int], Dict[int, int], Dict[str, int]]:
    """
    构建 user/item/type 词表
    :return: (user2idx, item2idx, type2idx), 0 预留给 padding/unknown
    """
    user2idx: Dict[str, int] = {"<pad>": 0}
    item2idx: Dict[int, int] = {0: 0}
    type2idx: Dict[str, int] = {"<pad>": 0}

    for r in user_records:
        u = r.get("user")
        if u and u not in user2idx:
            user2idx[u] = len(user2idx)

    for s in shopping_items:
        sid = s.get("shopping_id")
        if sid is not None:
            iid = int(sid)
            if iid not in item2idx:
                item2idx[iid] = len(item2idx)
        types = s.get("type") or []
        if isinstance(types, str):
            types = [types]
        for t in types:
            t_str = str(t)
            if t_str and t_str not in type2idx:
                type2idx[t_str] = len(type2idx)

    return user2idx, item2idx, type2idx

# 总结词表
def summarize_vocab(
    user2idx: Dict[str, int],
    item2idx: Dict[int, int],
    type2idx: Dict[str, int],
) -> Dict[str, int]:
    return {
        "users": max(0, len(user2idx) - 1),
        "items": max(0, len(item2idx) - 1),
        "types": max(0, len(type2idx) - 1),
    }

# 检测词汇表变化
def detect_vocab_changes(
    user_records: List[dict],
    shopping_items: List[dict],
    user2idx: Dict[str, int],
    item2idx: Dict[int, int],
    type2idx: Dict[str, int],
) -> Dict[str, bool]:
    has_new_user = False
    has_new_item = False
    has_new_type = False

    for record in user_records:
        user = record.get("user")
        if user and user not in user2idx:
            has_new_user = True
            break

    for item in shopping_items:
        sid = item.get("shopping_id")
        if sid is not None and int(sid) not in item2idx:
            has_new_item = True
            break

        types = item.get("type") or []
        if isinstance(types, str):
            types = [types]
        if any(str(type_name) not in type2idx for type_name in types if type_name):
            has_new_type = True
            break

    return {
        "has_new_user": has_new_user,
        "has_new_item": has_new_item,
        "has_new_type": has_new_type,
        "requires_full_rebuild": has_new_user or has_new_item or has_new_type,
    }

# 获取商品特征
def get_item_features(
    shopping_items: List[dict],
    item2idx: Dict[int, int],
    type2idx: Dict[str, int],
) -> Dict[int, Tuple[int, int, float]]:
    """
    :return: item_id -> (item_idx, type_idx, price_norm)
    """
    item_feats: Dict[int, Tuple[int, int, float]] = {}
    prices: List[float] = []
    for s in shopping_items:
        sid = s.get("shopping_id")
        if sid is None:
            continue
        iid = int(sid)
        types = s.get("type") or []
        if isinstance(types, str):
            types = [types]
        type_str = str(types[0]) if types else "<pad>"
        type_idx = type2idx.get(type_str, 0)
        spec_list = s.get("specification_list") or []
        price = float(spec_list[0].get("price", 0)) if spec_list else 0.0
        prices.append(price)
        item_feats[iid] = (item2idx.get(iid, 0), type_idx, price)

    # 价格归一化 (log1p)
    if prices:
        max_p = max(prices) or 1
        for iid, (idx, tidx, p) in list(item_feats.items()):
            item_feats[iid] = (idx, tidx, np.log1p(p) / np.log1p(max_p))

    return item_feats

# 过滤记录
def filter_records_after(
    user_records: List[dict],
    last_trained_at: str | None,
) -> List[dict]:
    cutoff = _parse_iso_datetime(last_trained_at)
    if cutoff is None:
        return list(user_records)

    out: List[dict] = []
    for record in user_records:
        updated_at = _parse_iso_datetime(record.get("updated_at"))
        if updated_at is not None and updated_at > cutoff:
            out.append(record)
    return out

# 获取最新记录时间戳
def get_latest_record_timestamp(user_records: List[dict]) -> str | None:
    latest: datetime | None = None
    for record in user_records:
        updated_at = _parse_iso_datetime(record.get("updated_at"))
        if updated_at is None:
            continue
        if latest is None or updated_at > latest:
            latest = updated_at
    return latest.isoformat() if latest else None

# 构建训练数据
def build_training_data(
    user_records: List[dict],
    shopping_items: List[dict],
    item_feats: Dict[int, Tuple[int, int, float]],
    user2idx: Dict[str, int],
    item2idx: Dict[int, int],
    negative_ratio: int = 4,
    favorites: List[dict] | None = None,
    favorite_repeat: int = 3,
) -> List[Tuple[int, int, int, int, float, int]]:
    """
    构建 (user_idx, item_idx, type_idx, price_norm, label) 训练样本
    正样本: 用户实际交互 + 收藏（收藏重复 favorite_repeat 次以提高权重）
    负样本: 随机采样
    """
    user_items: Dict[str, set] = defaultdict(set)
    all_items = set(item_feats.keys())

    for r in user_records:
        u = r.get("user")
        sid = _get_shopping_id(r)
        if u and sid is not None and sid in item_feats:
            user_items[u].add(sid)

    user_fav_items: Dict[str, set] = defaultdict(set)
    if favorites:
        for fav in favorites:
            u = fav.get("user")
            sid = fav.get("shopping_id")
            if u and sid is not None and int(sid) in item_feats:
                user_fav_items[u].add(int(sid))
                user_items[u].add(int(sid))

    samples = []
    for u, items in user_items.items():
        uidx = user2idx.get(u, 0)
        fav_set = user_fav_items.get(u, set())
        for iid in items:
            idx, tidx, pnorm = item_feats[iid]
            repeat = favorite_repeat if iid in fav_set else 1
            for _ in range(repeat):
                samples.append((uidx, idx, tidx, pnorm, 1))
        neg_pool = all_items - items
        n_neg = min(len(items) * negative_ratio, len(neg_pool))
        for iid in random.sample(list(neg_pool), n_neg):
            idx, tidx, pnorm = item_feats[iid]
            samples.append((uidx, idx, tidx, pnorm, 0))

    random.shuffle(samples)
    return samples

# 构建增量训练数据
def build_incremental_training_data(
    user_records: List[dict],
    item_feats: Dict[int, Tuple[int, int, float]],
    user2idx: Dict[str, int],
    negative_ratio: int = 4,
    favorites: List[dict] | None = None,
    favorite_repeat: int = 3,
) -> List[Tuple[int, int, int, float, int]]:
    """
    仅根据新增行为构建增量训练样本。
    只使用已存在词表内的 user/item，超出词表的情况应由外部触发全量重建。
    收藏记录重复 favorite_repeat 次以增强权重。
    """
    user_items: Dict[str, set[int]] = defaultdict(set)
    all_items = set(item_feats.keys())

    for record in user_records:
        user = record.get("user")
        sid = _get_shopping_id(record)
        if not user or user not in user2idx or sid is None or sid not in item_feats:
            continue
        user_items[user].add(sid)

    user_fav_items: Dict[str, set[int]] = defaultdict(set)
    if favorites:
        for fav in favorites:
            u = fav.get("user")
            sid = fav.get("shopping_id")
            if not u or u not in user2idx or sid is None or int(sid) not in item_feats:
                continue
            user_fav_items[u].add(int(sid))
            user_items[u].add(int(sid))

    samples: List[Tuple[int, int, int, float, int]] = []
    for user, items in user_items.items():
        user_idx = user2idx.get(user, 0)
        fav_set = user_fav_items.get(user, set())
        for item_id in items:
            item_idx, type_idx, price_norm = item_feats[item_id]
            repeat = favorite_repeat if item_id in fav_set else 1
            for _ in range(repeat):
                samples.append((user_idx, item_idx, type_idx, price_norm, 1))

        neg_pool = list(all_items - items)
        neg_count = min(len(items) * negative_ratio, len(neg_pool))
        if neg_count <= 0:
            continue
        for item_id in random.sample(neg_pool, neg_count):
            item_idx, type_idx, price_norm = item_feats[item_id]
            samples.append((user_idx, item_idx, type_idx, price_norm, 0))

    random.shuffle(samples)
    return samples

# 保存词表
def save_vocab(
    user2idx: Dict[str, int],
    item2idx: Dict[int, int],
    type2idx: Dict[str, int],
    path: str,
) -> None:
    """保存词表到 JSON"""
    # 将 key 转为 str 以便 JSON 序列化
    data = {
        "user2idx": user2idx,
        "item2idx": {str(k): v for k, v in item2idx.items()},
        "type2idx": type2idx,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 加载词表
def load_vocab(path: str) -> Tuple[Dict[str, int], Dict[int, int], Dict[str, int]]:
    """加载词表"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    item2idx = {int(k): v for k, v in data["item2idx"].items()}
    return data["user2idx"], item2idx, data["type2idx"]
