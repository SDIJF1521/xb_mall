"""
Wide & Deep 模型结构
Wide: 线性部分, 学习 user-item 交叉记忆
Deep: 嵌入 + MLP, 学习特征泛化
输出: P(点击/购买|user,item) = sigmoid(wide_out + deep_out)
"""
import torch
import torch.nn as nn
from typing import Dict, Any


class WideDeepModel(nn.Module):
    """Wide & Deep 推荐模型"""

    def __init__(
        self,
        n_users: int,
        n_items: int,
        n_types: int,
        user_emb_dim: int = 32,
        item_emb_dim: int = 32,
        type_emb_dim: int = 8,
        deep_hidden: tuple = (128, 64, 32),
        dropout: float = 0.2,
    ):
        super().__init__()
        self.n_users = n_users
        self.n_items = n_items
        self.n_types = n_types

        # Wide 部分: user 与 item 的交叉 (通过两个嵌入 + 内积 近似交叉)
        self.wide_user_emb = nn.Embedding(n_users + 1, 1, padding_idx=0)
        self.wide_item_emb = nn.Embedding(n_items + 1, 1, padding_idx=0)
        self.wide_bias = nn.Parameter(torch.zeros(1))

        # Deep 部分: 嵌入层
        self.deep_user_emb = nn.Embedding(n_users + 1, user_emb_dim, padding_idx=0)
        self.deep_item_emb = nn.Embedding(n_items + 1, item_emb_dim, padding_idx=0)
        self.deep_type_emb = nn.Embedding(n_types + 1, type_emb_dim, padding_idx=0)

        # 价格标量 (1维)
        deep_input_dim = user_emb_dim + item_emb_dim + type_emb_dim + 1

        # Deep MLP
        layers = []
        prev = deep_input_dim
        for h in deep_hidden:
            layers.extend([
                nn.Linear(prev, h),
                nn.ReLU(),
                nn.BatchNorm1d(h),
                nn.Dropout(dropout),
            ])
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.deep_mlp = nn.Sequential(*layers)

    def forward(
        self,
        user_idx: torch.Tensor,
        item_idx: torch.Tensor,
        type_idx: torch.Tensor,
        price_norm: torch.Tensor,
    ) -> torch.Tensor:
        """
        :param user_idx: [B]
        :param item_idx: [B]
        :param type_idx: [B]
        :param price_norm: [B] 归一化价格
        :return: [B] 点击/购买概率
        """
        # Wide: 线性组合 (等价于交叉特征的线性)
        wide_user = self.wide_user_emb(user_idx).squeeze(-1)
        wide_item = self.wide_item_emb(item_idx).squeeze(-1)
        wide_out = wide_user + wide_item + self.wide_bias

        # Deep: 嵌入拼接 + MLP
        u_emb = self.deep_user_emb(user_idx)
        i_emb = self.deep_item_emb(item_idx)
        t_emb = self.deep_type_emb(type_idx)
        price_feat = price_norm.unsqueeze(-1)
        deep_in = torch.cat([u_emb, i_emb, t_emb, price_feat], dim=-1)
        deep_out = self.deep_mlp(deep_in).squeeze(-1)

        return torch.sigmoid(wide_out + deep_out)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "WideDeepModel":
        return cls(
            n_users=config["n_users"],
            n_items=config["n_items"],
            n_types=config["n_types"],
            user_emb_dim=config.get("user_emb_dim", 32),
            item_emb_dim=config.get("item_emb_dim", 32),
            type_emb_dim=config.get("type_emb_dim", 8),
            deep_hidden=tuple(config.get("deep_hidden", [128, 64, 32])),
            dropout=config.get("dropout", 0.2),
        )
