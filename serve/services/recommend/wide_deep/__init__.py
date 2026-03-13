"""
Wide & Deep 推荐模型
参考: Wide & Deep Learning for Recommender Systems (Google, 2016)
- Wide: 线性模型 + 交叉特征, 记忆历史共现
- Deep: 深度网络 + 嵌入, 泛化到未见特征组合
"""
from .model import WideDeepModel
from .inference import WideDeepRecommender

__all__ = ["WideDeepModel", "WideDeepRecommender"]
