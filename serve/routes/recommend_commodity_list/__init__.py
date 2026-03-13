from typing import Annotated
from random import choice

from aiomysql import Connection
from fastapi import APIRouter, Depends, Query, Header

from services.user_info import UserInfo
from services.cache_service import CacheService
from services.recommend import RecommendCommodity

from data.sql_client_pool import get_db_pool, db_pool
from data.redis_client import get_redis, RedisClient
from data.file_client import read_file_base64_with_cache
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()


async def _build_output_list(id_list: list, mongodb: MongoDBClient, redis: RedisClient) -> list:
    """根据商品ID列表构建输出格式"""
    mongo_data = [await mongodb.find_one('shopping', {'shopping_id': i}) for i in id_list]
    mongo_data = [i for i in mongo_data if i]
    out_list = []
    for i in mongo_data:
        info = i.get('info', '')
        out_list.append({
            'mall_id': i['mall_id'],
            'shopping_id': i['shopping_id'],
            'name': i['name'],
            'info': info if len(info) <= 50 else info[:50] + '...',
            'type': i.get('type', []),
            'price': i['specification_list'][0]['price'] if i.get('specification_list') else 0,
            'img': await read_file_base64_with_cache(i['img_list'][0], redis) if i.get('img_list') else '',
        })
    return out_list


@router.get("/recommend_commodity_list")
async def recommend_commodity_list(
    access_token: Annotated[str, Header()] = None,
    page: int = Query(1, description='页码'),
    db: Connection = Depends(get_db_pool),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    '''获取推荐商品列表 (已登录用户使用AI推荐，未登录使用随机推荐)'''
    sql = db_pool
    cache = CacheService(redis)

    async def execute():
        """随机推荐 (未登录或无历史时)"""
        commodity_id_list = await sql.execute_query('select shopping_id from shopping where audit = 1')
        if not commodity_id_list:
            return {'code': 404, 'msg': '暂无商品', 'success': False}
        select_id_list = [i[0] for i in commodity_id_list]
        vlu = min(12, len(select_id_list))
        id_list = [select_id_list.pop(select_id_list.index(choice(select_id_list))) for _ in range(vlu)]
        out_list = await _build_output_list(id_list, mongodb, redis)
        out = {'code': 200, 'msg': '成功', 'data': out_list, 'success': True}
        await cache.set(f'recommend_commodity_list:{page}', out, expire=60 * 5)
        return out

    if access_token is None:
        return await execute()

    user_info = UserInfo(access_token)
    verify_token = await user_info.token_analysis()
    if not verify_token.get('current'):
        return await execute()

    # 已登录: 尝试AI推荐
    recommend_svc = RecommendCommodity(mongodb)
    id_list = await recommend_svc._index_recommend_commodity(verify_token['user'])
    if id_list:
        out_list = await _build_output_list(id_list, mongodb, redis)
        cache_key = f'recommend_commodity_list:user:{verify_token["user"]}:{page}'
        out = {'code': 200, 'msg': '成功', 'data': out_list, 'success': True}
        await cache.set(cache_key, out, expire=60 * 5)
        return out

    return await execute()