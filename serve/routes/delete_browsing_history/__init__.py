"""DELETE /browsing_history 删除当前用户某条浏览记录（需登录）"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.record import Record
from services.user_info import UserInfo
from data.redis_client import get_redis, RedisClient
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()


@router.delete('/browsing_history')
async def delete_browsing_history(
    shopping_id: int = Query(..., description='要删除的商品ID'),
    access_token: Annotated[str | None, Header()] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """删除当前用户的某条浏览记录，同时失效相关 Redis 缓存。"""
    if not access_token:
        return {'code': 401, 'msg': '请先登录', 'success': False}

    user_info = UserInfo(access_token)
    verify = await user_info.token_analysis()
    if not verify.get('current'):
        return {'code': 401, 'msg': verify.get('msg', 'token无效'), 'success': False}

    user = verify['user']
    recorder = Record(mongodb, redis_client=redis)

    deleted = await mongodb.delete_one(
        Record.COLLECTION_NAME,
        {'user': user, 'shopping_id': shopping_id},
    )
    await recorder.clear_user_cache(user)

    if deleted:
        return {'code': 200, 'msg': '删除成功', 'success': True}
    return {'code': 404, 'msg': '记录不存在', 'success': False}
