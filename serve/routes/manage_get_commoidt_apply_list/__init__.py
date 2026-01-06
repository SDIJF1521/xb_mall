import base64
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Query,Header,HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client
from data.data_mods import ManageGetCommodityApplyList

router = APIRouter()

@router.get('/manage_get_commoidt_apply_list')
async def manage_get_commoidt_apply(data:Annotated[ManageGetCommodityApplyList,Query(...)],
                                    access_token:str = Header(...),
                                    db:Connection=Depends(get_db),
                                    redis:RedisClient=Depends(get_redis),
                                    mongodb:MongoDBClient=Depends(get_mongodb_client)):
    """
    管理员获取商品上架申请列表
    """
    verify = ManagementTokenVerify(token=access_token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()

    async def execute():
        cache = CacheService(redis)
        page_size = 20
        page = data.page if data.page and data.page > 0 else 1
        offset = (page - 1) * page_size
        
        if data.select_data is None or not data.select_data.strip():
            cache_key = cache._make_key('admin:commodity:apply', page)
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
            mongodb_data = await mongodb.find_many('shopping', {'audit': 0}, limit=page_size, skip=offset)
            total_count = await execute_db_query(db, 'select count(*) from shopping where audit = 0')
            total = total_count[0][0] if total_count and len(total_count) > 0 and len(total_count[0]) > 0 else 0
            
            if mongodb_data:
                out = []
                for i in mongodb_data:
                    out.append({
                        'mall_id': i['mall_id'],
                        'shopping_id': i['shopping_id'],
                        'name': i['name'],
                        'types': i.get('type', []),
                        'info': i['info'],
                        'time': i['time']
                    })
                result = {'current': True, 'commodity_list': out, 'page': total}
                await cache.set(cache_key, result, expire=60)
                return result
            else:
                return {'current': True, 'commodity_list': [], 'page': 0}
        else:
            search_query = {
                'name': {'$regex': data.select_data.strip(), '$options': 'i'},
                'audit': 0
            }
            
            all_matching = await mongodb.find_many('shopping', search_query)
            total = len(all_matching) if all_matching else 0
            
            mongodb_data = await mongodb.find_many('shopping', search_query, limit=page_size, skip=offset)
            out = []
            if mongodb_data:
                for i in mongodb_data:
                    out.append({
                        'mall_id': i['mall_id'],
                        'shopping_id': i['shopping_id'],
                        'name': i['name'],
                        'types': i.get('type', []),
                        'info': i['info'],
                        'time': i['time']
                    })
                return {'current': True, 'commodity_list': out, 'page': total}
            else:
                return {'current': True, 'commodity_list': [], 'page': 0}

    try:
        sql_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
        Verify_data = await verify.run(sql_data)
        if Verify_data['current']:
            return await execute()
        else:
            return {'current':False,'msg':'验证失败','code':401}    
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))