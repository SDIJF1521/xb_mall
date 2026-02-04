from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import GetMallName


router = APIRouter()

@router.post('/get_mall_name')
async def buyer_get_mall_name(data:Annotated[GetMallName,Form()] ,db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):
    """获取店铺名称列表"""
    try:
        verify_duter_token = VerifyDuterToken(data.token,redis)
        token_data = await verify_duter_token.token_data()
        cache = CacheService(redis)
        
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            mall_name = []
            if data.mall_name is None:
                if verify_data[0]:
                    cache_key = cache._make_key('mall_name:user', token_data.get('user'))
                    cached_data = await cache.get(cache_key)
                    if cached_data:
                        return cached_data
                    
                    sql_data = await execute_db_query(db,'select mall_id,mall_name,creation_time from store where user = %s',(token_data.get('user')))
                    if sql_data:
                        for i in sql_data:
                            mall_name.append({'id':i[0],'mall_name':i[1],'creation_time':i[2]})
                    result = {'mall_name':mall_name,'current':True}
                    await cache.set(cache_key, result, expire=300)
                    return result
                else:
                    return {'error':'token 验证失败','current':False}
            else:
                # 使用模糊搜索
                sql_data = await execute_db_query(db,'select mall_id,mall_name,creation_time from store where user = %s and mall_name LIKE %s',(token_data.get('user'),f'%{data.mall_name}%'))
                if sql_data:
                    for i in sql_data:
                        mall_name.append({'id':i[0],'mall_name':i[1],'creation_time':i[2]})
                    return {'mall_name':mall_name,'current':True}
                else:
                    return {'error':'该店铺不存在','current':False}
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
            mall_name = []
            if data.mall_name is None:
                if execute_code[2] and verify_data[0]:
                    cache_key = cache._make_key('mall_name:mall', token_data.get('mall_id'))
                    cached_data = await cache.get(cache_key)
                    if cached_data:
                        return cached_data
                    
                    sql_data = await execute_db_query(db,'select mall_id,mall_name,creation_time from store where mall_id = %s',(token_data.get('mall_id')))
                    if sql_data:
                        for i in sql_data:
                            mall_name.append({'id':i[0],'mall_name':i[1],'creation_time':i[2]})
                    result = {'mall_name':mall_name,'current':True}
                    await cache.set(cache_key, result, expire=300)
                    return result
                else:
                    return {'error':'token 验证失败','current':False}
            else:
                return {'error':'该店铺不存在','current':False}
        
    except Exception as e:
        return {'error':str(e),'current':False}