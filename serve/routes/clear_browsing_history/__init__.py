"""DELETE /browsing_history/all 清空当前用户所有浏览记录（需登录）"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from services.record import Record
from services.user_info import UserInfo
from data.redis_client import get_redis, RedisClient
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()


@router.delete('/browsing_history/all')
async def clear_all_browsing_history(
    access_token: Annotated[str | None, Header()] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """清空当前用户所有浏览记录，同时失效相关 Redis 缓存。"""
    if not access_token:
        return {'code': 401, 'msg': '请先登录', 'success': False}

    user_info = UserInfo(access_token)
    verify = await user_info.token_analysis()
    if not verify.get('current'):
        return {'code': 401, 'msg': verify.get('msg', 'token无效'), 'success': False}

    user = verify['user']
    recorder = Record(mongodb, redis_client=redis)

    await mongodb.delete_many(Record.COLLECTION_NAME, {'user': user})
    await recorder.clear_user_cache(user)

    return {'code': 200, 'msg': '清空成功', 'success': True}
