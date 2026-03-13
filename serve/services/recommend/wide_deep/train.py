"""
Wide & Deep 训练脚本
用法 (在 serve 目录下执行):
  cd serve && python -m services.recommend.wide_deep.train
  python -m services.recommend.wide_deep.train --epochs 20 --batch-size 512
"""
import json
import logging
import random
import sys
from pathlib import Path
import asyncio

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# 添加 serve 目录到 path (用于导入 config)
# train.py -> wide_deep/ -> recommend/ -> services/ -> serve
_serve_dir = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_serve_dir))

from services.recommend.wide_deep.model import WideDeepModel
from services.recommend.wide_deep.dataset import (
    build_vocab,
    build_training_data,
    get_item_features,
    save_vocab,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "wide_deep"
DEFAULT_MODEL_DIR.mkdir(parents=True, exist_ok=True)


def _get_shopping_id(r: dict):
    sid = r.get("shopping_id") or r.get("commodity_id")
    return int(sid) if sid is not None else None


async def load_data_from_mongodb():
    """从 MongoDB 加载数据"""
    from pymongo import MongoClient
    from config.mongodb_config import settings

    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]

    user_records = list(db.user_browse_record.find({}))
    shopping_items = list(db.shopping.find({}))

    client.close()
    logger.info(f"加载 user_browse_record: {len(user_records)} 条, shopping: {len(shopping_items)} 条")
    return user_records, shopping_items


async def main(
    model_dir: str = None,
    epochs: int = 10,
    batch_size: int = 256,
    lr: float = 0.001,
    negative_ratio: int = 4,
):
    model_dir = Path(model_dir or DEFAULT_MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)

    user_records, shopping_items = await load_data_from_mongodb()
    if not user_records or not shopping_items:
        logger.warning("数据不足, 无法训练 Wide & Deep 模型")
        return

    user2idx, item2idx, type2idx = build_vocab(user_records, shopping_items)
    item_feats = get_item_features(shopping_items, item2idx, type2idx)

    samples = build_training_data(
        user_records, shopping_items, item_feats,
        user2idx, item2idx, negative_ratio=negative_ratio
    )
    if len(samples) < 100:
        logger.warning("训练样本过少, 建议积累更多用户行为数据后训练")
        return

    save_vocab(user2idx, item2idx, type2idx, str(model_dir / "vocab.json"))

    # 转为 Tensor
    users = torch.LongTensor([s[0] for s in samples])
    items = torch.LongTensor([s[1] for s in samples])
    types = torch.LongTensor([s[2] for s in samples])
    prices = torch.FloatTensor([s[3] for s in samples])
    labels = torch.FloatTensor([s[4] for s in samples]).unsqueeze(1)

    dataset = TensorDataset(users, items, types, prices, labels)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    n_users = len(user2idx) + 1
    n_items = len(item2idx) + 1
    n_types = len(type2idx) + 1

    model = WideDeepModel(
        n_users=n_users,
        n_items=n_items,
        n_types=n_types,
        user_emb_dim=32,
        item_emb_dim=32,
        type_emb_dim=8,
        deep_hidden=(128, 64, 32),
        dropout=0.2,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    model.train()
    for ep in range(epochs):
        total_loss = 0.0
        for u, i, t, p, y in loader:
            optimizer.zero_grad()
            pred = model(u, i, t, p)
            loss = criterion(pred.unsqueeze(1), y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(loader)
        logger.info(f"Epoch {ep+1}/{epochs} loss={avg_loss:.4f}")

    config = {
        "n_users": n_users,
        "n_items": n_items,
        "n_types": n_types,
        "user_emb_dim": 32,
        "item_emb_dim": 32,
        "type_emb_dim": 8,
        "deep_hidden": [128, 64, 32],
        "dropout": 0.2,
    }
    with open(model_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    torch.save(model.state_dict(), model_dir / "model.pt")
    logger.info(f"模型已保存到 {model_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--negative-ratio", type=int, default=4)
    args = parser.parse_args()
    asyncio.run(main(
        model_dir=args.model_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        negative_ratio=args.negative_ratio,
    ))
