"""
Wide & Deep 推理服务
加载训练好的模型, 对指定用户生成推荐列表
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

from .model import WideDeepModel
from .dataset import load_vocab

DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "wide_deep"


class WideDeepRecommender:
    """Wide & Deep 推荐推理"""

    def __init__(self, model_dir: str | Path = DEFAULT_MODEL_DIR):
        self.model_dir = Path(model_dir)
        self.model: Optional[WideDeepModel] = None
        self.user2idx: Dict[str, int] = {}
        self.item2idx: Dict[int, int] = {}
        self.idx2item: Dict[int, int] = {}
        self.type2idx: Dict[str, int] = {}
        self._item_feats: Dict[int, Tuple[int, int, float]] = {}
        self._loaded = False

    def load(self) -> bool:
        """加载模型和词表"""
        config_path = self.model_dir / "config.json"
        model_path = self.model_dir / "model.pt"
        vocab_path = self.model_dir / "vocab.json"

        if not config_path.exists() or not model_path.exists() or not vocab_path.exists():
            return False

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.model = WideDeepModel.from_config(config)
            self.model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
            self.model.eval()

            self.user2idx, self.item2idx, self.type2idx = load_vocab(str(vocab_path))
            self.idx2item = {v: k for k, v in self.item2idx.items() if k != 0}
            self._loaded = True
            return True
        except Exception:
            return False

    def set_item_features(self, item_feats: Dict[int, Tuple[int, int, float]]) -> None:
        """设置商品特征 (item_id -> (item_idx, type_idx, price_norm))"""
        self._item_feats = item_feats

    def _get_item_feat(self, item_id: int) -> Tuple[int, int, float]:
        idx = self.item2idx.get(item_id, 0)
        tidx = self.type2idx.get("<pad>", 0)
        return (idx, tidx, 0.0) if item_id not in self._item_feats else self._item_feats[item_id]

    def predict(
        self,
        user: str,
        candidate_item_ids: List[int],
        item_feats: Dict[int, Tuple[int, int, float]],
    ) -> List[Tuple[int, float]]:
        """
        对候选商品打分并排序
        :param user: 用户名
        :param candidate_item_ids: 候选商品 ID 列表
        :param item_feats: item_id -> (item_idx, type_idx, price_norm)
        :return: [(item_id, score), ...] 按分数降序
        """
        if not self._loaded or self.model is None:
            return []

        self.set_item_features(item_feats)
        uidx = self.user2idx.get(user, 0)
        if uidx == 0 and user not in self.user2idx:
            return []  # 未知用户

        scores = []
        with torch.no_grad():
            for iid in candidate_item_ids:
                idx, tidx, pnorm = self._get_item_feat(iid)
                u_t = torch.LongTensor([uidx])
                i_t = torch.LongTensor([idx])
                t_t = torch.LongTensor([tidx])
                p_t = torch.FloatTensor([pnorm])
                pred = self.model(u_t, i_t, t_t, p_t).item()
                scores.append((iid, pred))

        scores.sort(key=lambda x: -x[1])
        return scores

    def recommend(
        self,
        user: str,
        candidate_item_ids: List[int],
        item_feats: Dict[int, Tuple[int, int, float]],
        top_k: int = 12,
    ) -> List[int]:
        """推荐 top_k 个商品 ID"""
        scored = self.predict(user, candidate_item_ids, item_feats)
        return [iid for iid, _ in scored[:top_k]]
