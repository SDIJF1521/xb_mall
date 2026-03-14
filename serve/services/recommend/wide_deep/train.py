"""
Wide & Deep 训练脚本
用法 (在 serve 目录下执行):
  cd serve && python -m services.recommend.wide_deep.train
  python -m services.recommend.wide_deep.train --epochs 20 --batch-size 512
"""
import asyncio
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

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
    build_incremental_training_data,
    build_training_data,
    get_item_features,
    load_vocab,
)

logger = logging.getLogger("fastapi_logger")

DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "wide_deep"
DEFAULT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_MODEL_CONFIG = {
    "user_emb_dim": 32,
    "item_emb_dim": 32,
    "type_emb_dim": 8,
    "deep_hidden": [128, 64, 32],
    "dropout": 0.2,
}

# 获取商品ID
def _get_shopping_id(r: dict):
    sid = r.get("shopping_id") or r.get("commodity_id")
    return int(sid) if sid is not None else None

# 构建模型配置
def build_model_config(
    user2idx: dict[str, int],
    item2idx: dict[int, int],
    type2idx: dict[str, int],
) -> dict:
    return {
        "n_users": len(user2idx) + 1,
        "n_items": len(item2idx) + 1,
        "n_types": len(type2idx) + 1,
        **DEFAULT_MODEL_CONFIG,
    }

# 创建模型
def create_model(config: dict) -> WideDeepModel:
    return WideDeepModel.from_config(config)

# 原子写入JSON
def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=path.parent, encoding="utf-8", suffix=".tmp"
    ) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)

# 原子保存PyTorch模型
def _atomic_torch_save(path: Path, state_dict: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=path.parent, suffix=".tmp") as tmp:
        tmp_path = Path(tmp.name)
    try:
        torch.save(state_dict, tmp_path)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

# 保存训练 artifacts
def save_training_artifacts(
    model_dir: Path,
    model: WideDeepModel,
    config: dict,
    user2idx: dict[str, int],
    item2idx: dict[int, int],
    type2idx: dict[str, int],
) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(model_dir / "config.json", config)
    _atomic_write_json(
        model_dir / "vocab.json",
        {
            "user2idx": user2idx,
            "item2idx": {str(k): v for k, v in item2idx.items()},
            "type2idx": type2idx,
        },
    )
    _atomic_torch_save(model_dir / "model.pt", model.state_dict())

# 加载现有 artifacts
def load_existing_artifacts(
    model_dir: Path,
) -> tuple[WideDeepModel, dict, dict[str, int], dict[int, int], dict[str, int]]:
    config_path = model_dir / "config.json"
    model_path = model_dir / "model.pt"
    vocab_path = model_dir / "vocab.json"
    if not config_path.exists() or not model_path.exists() or not vocab_path.exists():
        raise FileNotFoundError("Wide & Deep 模型文件不完整")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    user2idx, item2idx, type2idx = load_vocab(str(vocab_path))
    model = create_model(config)
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    return model, config, user2idx, item2idx, type2idx

# 构建Tensor数据集
def build_tensor_dataset(samples: list[tuple[int, int, int, float, int]]) -> TensorDataset:
    users = torch.LongTensor([sample[0] for sample in samples])
    items = torch.LongTensor([sample[1] for sample in samples])
    types = torch.LongTensor([sample[2] for sample in samples])
    prices = torch.FloatTensor([sample[3] for sample in samples])
    labels = torch.FloatTensor([sample[4] for sample in samples]).unsqueeze(1)
    return TensorDataset(users, items, types, prices, labels)

# 拟合模型
def fit_model(
    model: WideDeepModel,
    samples: list[tuple[int, int, int, float, int]],
    epochs: int,
    batch_size: int,
    lr: float,
) -> list[float]:
    if len(samples) < 2:
        raise ValueError("训练样本不足，至少需要 2 条样本")

    dataset = build_tensor_dataset(samples)
    effective_batch_size = min(batch_size, len(samples))
    drop_last = len(samples) > effective_batch_size and len(samples) % effective_batch_size == 1
    loader = DataLoader(
        dataset,
        batch_size=effective_batch_size,
        shuffle=True,
        drop_last=drop_last,
    )

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()
    history: list[float] = []

    model.train()
    for ep in range(epochs):
        total_loss = 0.0
        batch_count = 0
        for u, i, t, p, y in loader:
            optimizer.zero_grad()
            pred = model(u, i, t, p)
            loss = criterion(pred.unsqueeze(1), y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            batch_count += 1
        avg_loss = total_loss / max(1, batch_count)
        history.append(avg_loss)
        logger.info(f"Epoch {ep+1}/{epochs} loss={avg_loss:.4f}")
    return history

# 从 MongoDB 加载数据
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

# 训练全量模型
def train_full_from_data(
    user_records: list[dict],
    shopping_items: list[dict],
    model_dir: str | Path = None,
    epochs: int = 10,
    batch_size: int = 256,
    lr: float = 0.001,
    negative_ratio: int = 4,
) -> dict:
    model_dir = Path(model_dir or DEFAULT_MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)

    if not user_records or not shopping_items:
        raise ValueError("数据不足, 无法训练 Wide & Deep 模型")

    user2idx, item2idx, type2idx = build_vocab(user_records, shopping_items)
    item_feats = get_item_features(shopping_items, item2idx, type2idx)
    samples = build_training_data(
        user_records,
        shopping_items,
        item_feats,
        user2idx,
        item2idx,
        negative_ratio=negative_ratio,
    )
    if len(samples) < 100:
        raise ValueError("训练样本过少, 建议积累更多用户行为数据后训练")

    config = build_model_config(user2idx, item2idx, type2idx)
    model = create_model(config)
    history = fit_model(model, samples, epochs=epochs, batch_size=batch_size, lr=lr)
    save_training_artifacts(model_dir, model, config, user2idx, item2idx, type2idx)
    logger.info(f"模型已保存到 {model_dir}")
    return {
        "mode": "full",
        "samples": len(samples),
        "epochs": epochs,
        "loss_history": history,
        "config": config,
    }

# 增量训练模型
def incremental_train_from_data(
    new_records: list[dict],
    shopping_items: list[dict],
    model_dir: str | Path = None,
    epochs: int = 3,
    batch_size: int = 256,
    lr: float = 0.0005,
    negative_ratio: int = 4,
) -> dict:
    model_dir = Path(model_dir or DEFAULT_MODEL_DIR)
    model, config, user2idx, item2idx, type2idx = load_existing_artifacts(model_dir)
    item_feats = get_item_features(shopping_items, item2idx, type2idx)
    samples = build_incremental_training_data(
        new_records,
        item_feats,
        user2idx,
        negative_ratio=negative_ratio,
    )
    if len(samples) < 10:
        raise ValueError("增量训练样本过少, 跳过本次微调")

    history = fit_model(model, samples, epochs=epochs, batch_size=batch_size, lr=lr)
    save_training_artifacts(model_dir, model, config, user2idx, item2idx, type2idx)
    logger.info(f"增量模型已保存到 {model_dir}")
    return {
        "mode": "incremental",
        "samples": len(samples),
        "epochs": epochs,
        "loss_history": history,
        "config": config,
    }

# 主函数
async def main(
    model_dir: str = None,
    epochs: int = 10,
    batch_size: int = 256,
    lr: float = 0.001,
    negative_ratio: int = 4,
):
    user_records, shopping_items = await load_data_from_mongodb()
    try:
        result = train_full_from_data(
            user_records,
            shopping_items,
            model_dir=model_dir,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            negative_ratio=negative_ratio,
        )
        logger.info(
            "Wide & Deep 全量训练完成 | mode=%s | samples=%s",
            result["mode"],
            result["samples"],
        )
    except ValueError as exc:
        logger.warning(str(exc))

# 主函数入口
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
