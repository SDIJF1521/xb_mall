import os
from typing import  Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Form

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import UpdateMallUser
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.patch('/buyer_user_amend')
async def buyer_user_amend(
    data:Annotated[UpdateMallUser,Form()],
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    """修改店铺用户信息"""
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        old_img_path = f'./buyer_use_img/{data.stroe_id}_{data.user}.png'
        await execute_db_query(db,'update store_user set user = %s,password = %s,authority = %s,email = %s where user = %s AND store_id = %s',
                                   (data.user_name,data.user_password,data.authority,data.email,data.user,data.stroe_id))
        cache = CacheService(redis)
        try:
            if os.path.exists(old_img_path):
                os.remove(old_img_path)
                img_cache_key = cache._make_key('img_base64', old_img_path)
                await cache.delete(img_cache_key)
        except:
            pass
        await cache.delete_pattern(f'role:{data.stroe_id}:*')
        await cache.delete_pattern(f'role:list:{data.stroe_id}:*')
        await cache.delete_pattern(f'user:list:{data.stroe_id}:*')
        await cache.delete_pattern(f'user:info:{data.stroe_id}:*')
        await cache.delete_pattern(f'role:ratio:{data.stroe_id}')
        return {"code":200,"msg":"success","data":None,'current':True}

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
            if execute_code[1] and execute_code[4] and verify_data:
                return await execute()
            else:
               return {"code":400,"msg":"权限不足","data":None,'current':False}
    except HTTPException as e:
        return {"code":e.status_code,"msg":e.detail,"data":None,'current':False}
    except Exception as e:
        return {"code":500,"msg":str(e),"data":None,'current':False}
