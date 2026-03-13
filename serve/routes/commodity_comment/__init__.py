"""POST /commodity_comment 发布商品评论（需登录，每人每商品限评一次）"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Header

from services.user_info import UserInfo
from services.cache_service import CacheService
from data.redis_client import get_redis, RedisClient
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()


@router.post('/commodity_comment')
async def commodity_comment(
    access_token: Annotated[str, Header()],
    shopping_id: int = Query(..., description='商品ID'),
    mall_id: int = Query(..., description='店铺ID'),
    rating: int = Query(5, ge=1, le=5, description='评分 1-5'),
    content: str = Query(..., min_length=1, max_length=500, description='评论内容'),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """发布商品评论，同一用户对同一商品只能评论一次"""
    user_info = UserInfo(access_token)
    verify = await user_info.token_analysis()
    if not verify.get('current'):
        return {'code': 401, 'msg': '请先登录', 'success': False}

    username = verify['user']

    doc = await mongodb.find_one(
        'shopping',
        {'mall_id': mall_id, 'shopping_id': shopping_id, 'audit': 1},
    )
    if not doc:
        return {'code': 404, 'msg': '商品不存在或已下架', 'success': False}

    existing = await mongodb.find_one(
        'commodity_comment',
        {'shopping_id': shopping_id, 'username': username},
    )
    if existing:
        return {'code': 400, 'msg': '您已评论过该商品', 'success': False}

    await mongodb.insert_one(
        'commodity_comment',
        {
            'shopping_id': shopping_id,
            'mall_id': mall_id,
            'username': username,
            'rating': rating,
            'content': content.strip(),
            'created_at': datetime.now().isoformat(),
        },
    )

    cache = CacheService(redis)
    await redis.delete(cache._make_key('commodity:comments', shopping_id, 1))

    return {'code': 200, 'msg': '评论发布成功', 'success': True}
