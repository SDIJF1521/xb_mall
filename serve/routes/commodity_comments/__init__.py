"""GET /commodity_comments 获取商品评论列表（公开接口，无需登录）"""
from fastapi import APIRouter, Depends, Query

from services.cache_service import CacheService
from data.redis_client import get_redis, RedisClient
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()


@router.get('/commodity_comments')
async def commodity_comments(
    shopping_id: int = Query(..., description='商品ID'),
    page: int = Query(1, ge=1, description='页码'),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取商品评论列表，每页 10 条，结果缓存 60 秒"""
    page_size = 10
    skip = (page - 1) * page_size

    cache = CacheService(redis)
    cache_key = cache._make_key('commodity:comments', shopping_id, page)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    comments_raw = await mongodb.find_many(
        'commodity_comment',
        {'shopping_id': shopping_id},
        limit=page_size,
        skip=skip,
    )
    total_list = await mongodb.find_many('commodity_comment', {'shopping_id': shopping_id})

    result = {
        'code': 200,
        'msg': '成功',
        'success': True,
        'total': len(total_list) if total_list else 0,
        'data': [
            {
                'id': str(c.get('_id', '')),
                'username': c.get('username', '匿名用户'),
                'rating': c.get('rating', 5),
                'content': c.get('content', ''),
                'created_at': c.get('created_at', ''),
            }
            for c in (comments_raw or [])
        ],
    }
    await cache.set(cache_key, result, expire=60)
    return result
