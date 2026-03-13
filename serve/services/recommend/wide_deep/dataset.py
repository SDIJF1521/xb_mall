"""
Wide & Deep 数据准备
从 user_browse_record 和 shopping 构建训练样本
"""
import json
import os
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np


def _get_shopping_id(r: dict) -> int | None:
    sid = r.get("shopping_id") or r.get("commodity_id")
    return int(sid) if sid is not None else None


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


def build_training_data(
    user_records: List[dict],
    shopping_items: List[dict],
    item_feats: Dict[int, Tuple[int, int, float]],
    user2idx: Dict[str, int],
    item2idx: Dict[int, int],
    negative_ratio: int = 4,
) -> List[Tuple[int, int, int, int, float, int]]:
    """
    构建 (user_idx, item_idx, type_idx, price_norm, label) 训练样本
    正样本: 用户实际交互; 负样本: 随机采样
    """
    user_items: Dict[str, set] = defaultdict(set)
    all_items = set(item_feats.keys())

    for r in user_records:
        u = r.get("user")
        sid = _get_shopping_id(r)
        if u and sid is not None and sid in item_feats:
            user_items[u].add(sid)

    samples = []
    for u, items in user_items.items():
        uidx = user2idx.get(u, 0)
        for iid in items:
            idx, tidx, pnorm = item_feats[iid]
            samples.append((uidx, idx, tidx, pnorm, 1))
        # 负采样
        neg_pool = all_items - items
        n_neg = min(len(items) * negative_ratio, len(neg_pool))
        for iid in random.sample(list(neg_pool), n_neg):
            idx, tidx, pnorm = item_feats[iid]
            samples.append((uidx, idx, tidx, pnorm, 0))

    random.shuffle(samples)
    return samples


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


def load_vocab(path: str) -> Tuple[Dict[str, int], Dict[int, int], Dict[str, int]]:
    """加载词表"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    item2idx = {int(k): v for k, v in data["item2idx"].items()}
    return data["user2idx"], item2idx, data["type2idx"]
