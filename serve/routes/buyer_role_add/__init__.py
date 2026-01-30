from typing import Annotated

from aiomysql import Connection

from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerRoleAdd
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.post('/buyer_role_add')
async def buyer_role_add(data:Annotated[BuyerRoleAdd,Form()],
                              db:Connection =Depends(get_db),
                              redis:RedisClient=Depends(get_redis)):
    """
    添加角色
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    
    async def execute():
        sql_select = 'select role from store_role where (mall_id = %s OR mall_id is Null) and role = %s'
        sql_data = await execute_db_query(db,sql_select,(data.stroe_id,data.role))
        
        sql_id_select = 'select max(id) from store_role where mall_id = %s or mall_id is Null'
        max_id = await execute_db_query(db,sql_id_select,(data.stroe_id))
        
        if not sql_data:
            new_role_id = max_id[0][0]+1 if max_id and max_id[0][0] else 1
            insert_sql = 'insert into store_role (id,role,mall_id,name) values (%s,%s,%s,%s)'
            await execute_db_query(db,insert_sql,(new_role_id,data.role,data.stroe_id,data.role_name))
            
            insert_authority_sql = 'insert into role_authority (mall_id,role_id,authority) values (%s,%s,%s)'
            await execute_db_query(db,insert_authority_sql,(data.stroe_id,new_role_id,data.role_authority))
            
            cache = CacheService(redis)
            await cache.delete_pattern(f'role:list:{data.stroe_id}')
            await cache.delete_pattern(f'role:ratio:{data.stroe_id}')
            await cache.delete(cache._make_key('role:info', new_role_id, data.stroe_id))
            
            return {"code":200,"msg":"添加成功","data":None,'current':True}
        else:
            return {"code":400,"msg":"角色已存在","data":None,'current':False}

    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
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
            if execute_code[0] and execute_code[1] and execute_code[4] and verify_data:
                return await execute()
            else:
                return {"code":400,"msg":"权限不足","data":None,'current':False}
    except HTTPException as e:
        return {"code":e.status_code,"msg":e.detail,"data":None,'current':False}
