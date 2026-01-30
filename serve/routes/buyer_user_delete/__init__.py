import os
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Form

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import DeleteMallUser
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()

@router.delete('/buyer_user_delete')
async def buyer_user_delete(data:Annotated[DeleteMallUser,Form()],
                            db:Connection=Depends(get_db),
                            redis:RedisClient=Depends(get_redis)):
    """删除店铺用户"""
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()    

    async def execute():
        cache = CacheService(redis)
        for i in data.user_name:
            img_query = await execute_db_query(db,'select img from store_user where store_id = %s and user=%s',(data.strore_id,i))
            await execute_db_query(db,'delete from store_user where store_id = %s and user=%s',(data.strore_id,i))
            
            try:
                if img_query and img_query[0][0]:
                    img_path = img_query[0][0]
                    if os.path.exists(img_path):
                        os.remove(img_path)
                    img_cache_key = cache._make_key('img_base64', img_path)
                    await cache.delete(img_cache_key)
            except:
                pass
        await cache.delete_pattern(f'user:list:{data.strore_id}:*')
        await cache.delete_pattern(f'user:info:{data.strore_id}:*')
        await cache.delete_pattern(f'role:ratio:{data.strore_id}')
        await cache.delete_pattern(f'role:{data.strore_id}:{data.user_name}')
        return {'code':200,'msg':'删除成功','current':True}
        
        
    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {'code':400,'msg':'用户不存在','current':False}
        else:
            role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                          db=db,
                                                          redis=redis,
                                                          name=token_data.get('user'),
                                                          mall_id=token_data.get('mall_id'))
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            
            if execute_code[3] and execute_code[4]:
                sql_data = await execute_db_query(db,'select user from store_user where store_id = %s and user = %s',(data.strore_id,token_data.get('user')))
                verify_data = await verify_duter_token.verify_token(sql_data)
                if verify_data:
                    if token_data.get('user') in data.user_name:
                        return {'code':400,'msg':'不能删除自己','current':False}
                    return await execute()
                else:
                    return {'code':400,'msg':'token验证失败','current':False}
            else:
                return {'code':400,'msg':'权限不足','current':False}
    except HTTPException as e:
        return {'code':400,'msg':e.detail,'current':False}
    except:
        return {'code':500,'msg':'无效参数','current':False}
            
