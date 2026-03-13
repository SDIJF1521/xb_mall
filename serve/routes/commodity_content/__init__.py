"""GET /commodity_detail 获取商品详情（登录后记录浏览行为，供推荐模型训练）"""
import asyncio
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Header

from services.user_info import UserInfo
from services.cache_service import CacheService
from data.redis_client import get_redis, RedisClient
from data.file_client import read_file_base64_with_cache
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()


async def _record_browse(user: str, shopping_id: int, mall_id: int, mongodb: MongoDBClient):
    """记录用户浏览行为（供推荐模型训练使用），写入失败不影响主流程"""
    try:
        existing = await mongodb.find_one(
            'user_browse_record',
            {'user': user, 'shopping_id': shopping_id},
        )
        now = datetime.now().isoformat()
        if existing:
            await mongodb.update_one(
                'user_browse_record',
                {'user': user, 'shopping_id': shopping_id},
                {'$set': {'updated_at': now}, '$inc': {'count': 1}},
            )
        else:
            await mongodb.insert_one(
                'user_browse_record',
                {
                    'user': user,
                    'shopping_id': shopping_id,
                    'mall_id': mall_id,
                    'count': 1,
                    'created_at': now,
                    'updated_at': now,
                },
            )
    except Exception:
        pass


@router.get('/commodity_detail')
async def commodity_detail(
    mall_id: int = Query(..., description='店铺ID'),
    shopping_id: int = Query(..., description='商品ID'),
    access_token: Annotated[str, Header()] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取商品详情（无需登录，登录后异步记录浏览行为）"""
    doc = await mongodb.find_one(
        'shopping',
        {'mall_id': mall_id, 'shopping_id': shopping_id, 'audit': 1},
    )
    if not doc:
        return {'code': 404, 'msg': '商品不存在或已下架', 'success': False}

    img_tasks = [
        read_file_base64_with_cache(path, redis, cache_expire=3600)
        for path in doc.get('img_list', [])
    ]
    img_list = await asyncio.gather(*img_tasks)

    if access_token:
        user_info = UserInfo(access_token)
        verify = await user_info.token_analysis()
        if verify.get('current'):
            asyncio.create_task(
                _record_browse(verify['user'], shopping_id, mall_id, mongodb)
            )

    return {
        'code': 200,
        'msg': '成功',
        'success': True,
        'data': {
            'mall_id': doc['mall_id'],
            'shopping_id': doc['shopping_id'],
            'name': doc.get('name', ''),
            'info': doc.get('info', ''),
            'type': doc.get('type', []),
            'img_list': [img for img in img_list if img],
            'specification_list': doc.get('specification_list', []),
        },
    }
