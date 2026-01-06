from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerRoleUpdate
from data.sql_client import execute_db_query,get_db
from data.redis_client import RedisClient,get_redis


router = APIRouter()

@router.patch('/buyer_update_role')
async def update_role(data:Annotated[BuyerRoleUpdate,Form()],
                      db:Connection = Depends(get_db),
                      redis:RedisClient = Depends(get_redis)):
    """
    更新角色信息
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        select_sql = "select role from store_role where id = %s and mall_id = %s"
        role_data = await execute_db_query(db,select_sql,(data.role_id,data.stroe_id))
        if role_data:
            sql = "update store_role set role = %s,name=%s where id = %s and mall_id = %s"
            await execute_db_query(db,sql,(data.role,data.role_name,data.role_id,data.stroe_id))
            sql_authority = "update role_authority set authority = %s where role_id = %s and mall_id = %s"
            await execute_db_query(db,sql_authority,(data.role_authority,data.role_id,data.stroe_id))
            cache = CacheService(redis)
            await cache.delete(cache._make_key('role:info', data.role_id, data.stroe_id))
            await cache.delete_pattern(f'role:list:{data.stroe_id}:*')
            await cache.delete_pattern(f'role:ratio:{data.stroe_id}')
            return {'code':200,'msg':'更新成功','current':True}
        else:
            return {'code':400,'msg':'角色不存在','current':False}

    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            return {'code':400,'msg':'token验证失败','current':False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code[1] and execute_code[4] and verify_data:
            return await execute()
        else:
            return {'code':400,'msg':'权限不足','current':False}