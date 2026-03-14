"""GET /commodity_detail 获取商品详情（登录后记录浏览行为，供推荐模型训练）"""
import asyncio
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Header

from config.log_config import logger
from services.user_info import UserInfo
from services.record import Record
from data.redis_client import get_redis, RedisClient
from data.file_client import read_file_base64_with_cache
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()


async def _record_browse(
    user: str,
    shopping_id: int,
    mall_id: int,
    mongodb: MongoDBClient,
    redis: RedisClient,
):
    """记录用户浏览行为（供推荐模型训练使用），写入失败不影响主流程"""
    try:
        logger.info(f"[浏览记录] 开始写入 user={user} shopping_id={shopping_id} mall_id={mall_id}")
        recorder = Record(mongodb, redis_client=redis)
        result = await recorder.browse_record(user, shopping_id, mall_id)
        logger.info(f"[浏览记录] 写入结果={result} user={user} shopping_id={shopping_id}")
    except Exception as e:
        logger.error(f"[浏览记录] 写入异常 user={user} shopping_id={shopping_id} error={e}")


@router.get('/commodity_detail')
async def commodity_detail(
    background_tasks: BackgroundTasks,
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
        logger.info(f"[商品详情] token验证结果={verify} shopping_id={shopping_id}")
        if verify.get('current'):
            logger.info(f"[商品详情] 触发浏览记录 user={verify['user']} shopping_id={shopping_id}")
            background_tasks.add_task(
                _record_browse, verify['user'], shopping_id, mall_id, mongodb, redis
            )
    else:
        logger.info(f"[商品详情] 未携带token(未登录) shopping_id={shopping_id}")

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
