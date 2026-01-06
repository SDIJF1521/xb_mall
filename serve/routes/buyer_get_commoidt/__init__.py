import base64
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Query,Header,HTTPException


from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService
from data.file_client import read_file_base64_with_cache

from data.data_mods import CommodityList
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client
import asyncio

router = APIRouter()

@router.get("/buyer_get_commoidt")
async def buyer_get_commoidt(
                            data:Annotated[CommodityList,Query(...)],
                            access_token:str = Header(...),
                            db:Connection=Depends(get_db),
                            redis:RedisClient=Depends(get_redis),
                            mongodb:MongoDBClient=Depends(get_mongodb_client)):
    """获取商品列表"""
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()
    offset = (data.page - 1) * 20 
    
    async def execute():
        cache = CacheService(redis)
        cache_key = None
        
        if data.select is not None and data.select.strip():
            search_pattern = data.select.strip()
            cache_key = cache._make_key('commodity:search', data.stroe_id, search_pattern, data.page)
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
            
            mongodb_filter = {
                'mall_id': data.stroe_id,
                'name': {'$regex': search_pattern, '$options': 'i'}
            }
            all_mongodb_commoidt_info = await mongodb.find_many('shopping', mongodb_filter)
            
            if all_mongodb_commoidt_info:
                shopping_ids = [item['shopping_id'] for item in all_mongodb_commoidt_info]
                total_count = len(shopping_ids)
                paginated_shopping_ids = shopping_ids[offset:offset + 20]
                
                if paginated_shopping_ids:
                    paginated_ids_set = set(paginated_shopping_ids)
                    mongodb_commoidt_info = [item for item in all_mongodb_commoidt_info if item['shopping_id'] in paginated_ids_set]
                    
                    placeholders = ','.join(['%s'] * len(paginated_shopping_ids))
                    sql_commoidt_info = await execute_db_query(db,
                                                            f'select * from shopping where mall_id = %s and shopping_id in ({placeholders})',
                                                            (data.stroe_id, *paginated_shopping_ids))
                else:
                    mongodb_commoidt_info = []
                    sql_commoidt_info = []
                
                n = [[total_count]]
            else:
                mongodb_commoidt_info = []
                sql_commoidt_info = []
                n = [[0]]
        else:
            cache_key = cache._make_key('commodity:list', data.stroe_id, data.page)
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
            
            mongodb_commoidt_info = await mongodb.find_many('shopping', {'mall_id': data.stroe_id}, limit=20, skip=offset)
            n = await execute_db_query(db, 'select count(*) from shopping where mall_id = %s', (data.stroe_id,))
            
            sql_commoidt_info = await execute_db_query(db,
                                                    'select * from shopping where mall_id = %s LIMIT %s,%s',
                                                    (data.stroe_id, offset, 20))
        
        if mongodb_commoidt_info and sql_commoidt_info:
            mongodb_sql_dic = {i['shopping_id']:{
                                                    'name':i['name'],
                                                    'types':i['type'],
                                                    'info':i['info'],
                                                    'img_list':i['img_list'],
                                                    'specification_list':i['specification_list']
                                                 } for i in mongodb_commoidt_info}
            out = []
            for i in sql_commoidt_info:

                img_tasks = [
                    read_file_base64_with_cache(j, redis, cache_expire=3600)
                    for j in mongodb_sql_dic[i[1]]['img_list']
                ]
                img_list = await asyncio.gather(*img_tasks)
                content = {
                    'id':i[1],
                    'name':mongodb_sql_dic[i[1]]['name'],
                    'classify_categorize':i[2],
                    'types':mongodb_sql_dic[i[1]]['types'],
                    'info':mongodb_sql_dic[i[1]]['info'],
                    'img_list':img_list,
                    'specification_list':mongodb_sql_dic[i[1]]['specification_list'],
                    'audit':i[4] if len(i) > 4 else 0,
                    'time':i[3]
                }
                out.append(content)

            result = {'code':200,'msg':'获取成功','success':True,'data':out,'page':n[0][0]}
        elif data.select is not None and data.select.strip():

            result = {'code':200,'msg':'获取成功','success':True,'data':[],'page':0}
        else:
            result = {'code':404,'msg':'获取失败','success':False}
        
        if cache_key:
            expire = 60 if (data.select is not None and data.select.strip()) else 300
            try:
                await cache.set(cache_key, result, expire=expire)
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"缓存已设置 | Key: {cache_key} | Expire: {expire}s")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"缓存设置异常 | Key: {cache_key} | 错误: {str(e)}")
        
        return result

    if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {'code':403,'msg':'验证失败','success':False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code[2] and verify_data:
            return await execute()
        else:
             return {'code':403,'msg':'权限不足','success':False}
