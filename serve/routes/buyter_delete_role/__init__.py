from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Form

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerRoleDelete
from data.redis_client import RedisClient,get_redis
from data.sql_client import execute_db_query,get_db

router = APIRouter()

@router.delete("/buyer_role_delete")
async def buyer_role_delete(data:Annotated[BuyerRoleDelete,Form()],
                            db:Connection = Depends(get_db),
                            redis:RedisClient = Depends(get_redis)):
    """
    删除角色
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        cache = CacheService(redis)
        for role_id in data.role_id:
            await execute_db_query(db,
                                   "delete from store_role where id=%s and (mall_id=%s or mall_id is null)",
                                   (role_id,data.stroe_id))
            await execute_db_query(db,
                                   "delete from role_authority where role_id=%s and (mall_id=%s or mall_id is null)",
                                   (role_id,data.stroe_id))
        
        for role_id in data.role_id:
            await cache.delete(cache._make_key('role:info', role_id, data.stroe_id))
        await cache.delete_pattern(f'role:list:{data.stroe_id}')
        await cache.delete_pattern(f'role:ratio:{data.stroe_id}')
        await cache.delete_pattern(f'user:list:{data.stroe_id}:*')
        return {"code":200,"msg":"操作成功","data":None,'current':True}
    try:
        if token_data.get('station') == '1':
                sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
                verify_data = await verify_duter_token.verify_token(sql_data)
                if verify_data[0]:
                    if data.strore_id not in token_data.get('mall_id_list'):
                        return {'code':403,'msg':'您没有权限执行此操作','success':False}
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
            if execute_code[3] and execute_code[4] and verify_data[0]:
                if data.strore_id != token_data.get('mall_id'):
                    return {'code':403,'msg':'您没有权限执行此操作','success':False}
                return await execute()
            else:
                return {"code":400,"msg":"您没有权限操作","data":None,'current':False}
    except HTTPException as e:
        return {"code":400,"msg":str(e),"data":None,'current':False}