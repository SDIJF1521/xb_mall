from typing import Annotated

from fastapi import APIRouter,Depends,Form,HTTPException
from aiomysql import Connection

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService
from data.file_client import read_file_base64_with_cache

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import GetMallUserList


router = APIRouter()

@router.post('/buyer_mall_user_list')
async def buyer_mall_user_list(data:Annotated[GetMallUserList,Form()],db:Connection = Depends(get_db),redis:RedisClient = Depends(get_redis)):
    """
    获取店铺用户列表
    """
    async def execute(id,page):
        cache = CacheService(redis)
        cache_key = cache._make_key('user:list', id, page)
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        sql_page = await execute_db_query(db,'select count(*) from store_user where store_id = %s',(id))
        if sql_page:
            if page > sql_page[0][0]:
                return {'code':400,'msg':'超出最大页数','current':False}
        offset = (page - 1) * 20
        limit = 20
        sql_user_list = await execute_db_query(db,'select * from store_user where store_id = %s LIMIT %s,%s',(id,offset,limit)) 
        if sql_user_list:
            data = [{'user':i[1],'password':i[2],'authority':i[3],'email':i[4],'img':i[5] if i[5] is not None else './buyer_use_img/通用/通用.png'}for i in sql_user_list]
            import asyncio
            img_tasks = [
                read_file_base64_with_cache(i['img'], redis, cache_expire=3600)
                for i in data
            ]
            img_results = await asyncio.gather(*img_tasks)
            for i, encoded_string in zip(data, img_results):
                i['img'] = encoded_string
            result = {'code':200,'msg':'获取成功','data':data,'current':True,'page':sql_page[0][0]}
            await cache.set(cache_key, result, expire=180)
            return result
        else:
            return {'code':400,'msg':'店铺不存在用户','current':False}

    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data[0]:
                if data.id not in token_data.get('state_id_list'):
                    return {'code':403,'msg':'您没有权限执行此操作','success':False}
                return await execute(data.id,data.page)
            else:
                return {'code':400,'msg':'token验证失败','current':False}

        else:
            role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                          db=db,
                                                          redis=redis,
                                                          name=token_data.get('user'),
                                                          mall_id=token_data.get('mall_id'))
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if execute_code[1] and execute_code[4] and verify_data[0]:
                if data.id != token_data.get('mall_id'):
                    return {'code':403,'msg':'您没有权限执行此操作','success':False}
                return await execute(data.id,data.page)
            else:
                return {'code':400,'msg':'权限不足'}
    except HTTPException as e:
        return {'code':e.status_code,'msg':e.detail,'current':False}

        
