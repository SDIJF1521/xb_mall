from typing import Annotated
from random import  choice


from aiomysql import Connection
from fastapi import APIRouter,Depends,Query,Header

from services.user_info import UserInfo
from services.cache_service import CacheService

from data.sql_client_pool import get_db_pool,db_pool
from data.redis_client import get_redis,RedisClient
from data.file_client import read_file_base64_with_cache
from data.mongodb_client import get_mongodb_client,MongoDBClient

router = APIRouter()

@router.get("/recommend_commodity_list")
async def recommend_commodity_list(
                                   access_token:Annotated[str, Header()]=None,
                                   page:int = Query(1,description='页码'),
                                   db:Connection = Depends(get_db_pool),
                                   redis:RedisClient = Depends(get_redis),
                                   mongodb:MongoDBClient = Depends(get_mongodb_client)
                                    ):
    '''
    获取推荐商品列表
    '''
    sql = db_pool
    
    async def execute():
        cache = CacheService(redis)
        commodity_id_list = await sql.execute_query('select shopping_id from shopping where audit = 1')
        if commodity_id_list:
            select_id_list = [i[0] for i in commodity_id_list]

            vlu = 12 if len(select_id_list)>=12 else len(select_id_list)
            id_list = [select_id_list.pop(select_id_list.index(choice(select_id_list))) for i in range(vlu)]
            mongo_data = [await mongodb.find_one('shopping',{'shopping_id':i}) for i in id_list]
            out_list = [{'mall_id':i['mall_id'],
                         'shopping_id':i['shopping_id'],
                         'name':i['name'],
                         'info': i['info'] if len(i['info']) <= 50 else i['info'][:50]+'...',
                         'type': i['type'],
                         'price': i['specification_list'][0]['price'],
                         'img': await read_file_base64_with_cache(i['img_list'][0], redis) if i['img_list'] and len(i['img_list']) > 0 else '',
                        } for i in mongo_data]
            print(out_list)
            out = {'code':200,'msg':'成功','data':out_list,'success':True}
            await cache.set(f'recommend_commodity_list:{page}',out,expire=60*5)
            return out
        else:
            return {'code':404,'msg':'暂无商品','success':False}


    if access_token is None:
        return await execute()
    else:
        user_info = UserInfo(access_token)
        verify_token = await user_info.token_analysis()
        if verify_token['"current']:
            return await execute()
        else:
            return {'code':401,'msg':'token无效','success':False}