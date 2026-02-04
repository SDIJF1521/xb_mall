from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,HTTPException,Depends,Form

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerGetRole
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.post('/buyer_get_role')
async def change_user_role(
    data:Annotated[BuyerGetRole,Form()],
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    """获取角色列表"""
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute(id,select_data:str = None):
        cache = CacheService(redis)
        cache_key = cache._make_key('role:list', id, select_data)
        
        if select_data is None:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        
        if select_data is not None:
            query = """
            SELECT * FROM store_role WHERE (mall_id = %s OR mall_id is Null) AND (role = %s OR name = %s)
            """
            result = await execute_db_query(db, query, (id, select_data,select_data))
        else:
            query = """
            SELECT * FROM store_role WHERE mall_id = %s OR mall_id is Null
            """
            result = await execute_db_query(db, query, (id))
        
        data = {}
        if result:
            data = [{i[0]:[i[1],i[3],i[2]]} for i in result]
            result_data = {'code':200,'msg':'操作成功','data':data,'current':True}
            if select_data is None:
                await cache.set(cache_key, result_data, expire=300)
            return result_data
        else:
            return {'code':400,'msg':'操作失败','data':data,'current':False}
    
    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data[0]:
            if data.stroe_id not in token_data.get('state_id_list'):
                return {'code':403,'msg':'您没有权限执行此操作','success':False}
            return await execute(data.stroe_id,data.select_data)
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
        if execute_code and len(execute_code) > 2 and execute_code[2] and verify_data[0]:
            if data.stroe_id != token_data.get('mall_id'):
                return {'code':403,'msg':'您没有权限执行此操作','success':False}
            return await execute(data.stroe_id,data.select_data)
        else:
            return {'code':400,'msg':'权限不足','data':data,'current':False}
        
