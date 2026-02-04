import asyncio
import logging
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Form,Depends,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService
from data.file_client import read_file_base64_with_cache

from data.data_mods import SelectMallUser
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('/buyer_user_select')
async def buyer_user_select(data:Annotated[SelectMallUser,Form()],db:Connection = Depends(get_db),redis:RedisClient = Depends(get_redis)):
    """查询指定店铺用户信息"""
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    
    # 检查token是否有效
    if not token_data:
        return {'code':400,'msg':'token无效或已过期','current':False}

    async def execute(id,user):
        cache = CacheService(redis)
        # 使用模糊搜索，缓存键包含搜索关键词
        cache_key = cache._make_key('user:search', id, user)
        
        async def fetch_store_user():
            # 使用 LIKE 进行模糊搜索
            sql_user = await execute_db_query(db,'select * from store_user where store_id = %s and user LIKE %s',
                                                (id, f'%{user}%'))
            if sql_user:
                user_data = [{'user':i[1],'password':i[2],'authority':i[3],'email':i[4],'img':i[5] if len(i) == 6 and i[5] is not None else './buyer_use_img/通用/通用.png'}for i in sql_user]
                # 使用异步文件读取，批量处理图片
                img_tasks = [
                    read_file_base64_with_cache(i['img'], redis, cache_expire=3600)
                    for i in user_data
                ]
                img_results = await asyncio.gather(*img_tasks)
                for i, encoded_string in zip(user_data, img_results):
                    i['img'] = encoded_string
                return {'code':200,'msg':'获取成功','data':user_data,'current':True}
            return None
        
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        result = await fetch_store_user()
        
        if result:
            # 缓存搜索结果，使用较短的过期时间
            await cache.set(cache_key, result, expire=60)
            return result
        else:            
            return {'code':400,'msg':'未找到匹配的用户','current':False}
        

    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data[0]:
                if data.strore_id not in token_data.get('state_id_list'):
                    return {'code':403,'msg':'您没有权限执行此操作','success':False}
                return await execute(data.strore_id,data.user_name)
            else:
                return {'code':400,'msg':'token验证失败','current':False}
        else:
            role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                          db=db,
                                                          redis=redis,
                                                          name=token_data.get('user'),
                                                          mall_id=token_data.get('mall_id'))
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            if not role_authority or len(role_authority) == 0 or len(role_authority[0]) == 0:
                return {'code':400,'msg':'权限验证失败','current':False}
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if execute_code and len(execute_code) > 4 and execute_code[2] and execute_code[4] and verify_data[0]:
                if data.strore_id != token_data.get('mall_id'):
                    return {'code':403,'msg':'您没有权限执行此操作','success':False}
                return await execute(data.strore_id,data.user_name)
            else:
                return {'code':400,'msg':'权限不足','current':False}
    except HTTPException as e:
        return {'code':e.status_code,'msg':e.detail,'current':False}
    except Exception as e:
        logger.error(f"buyer_user_select路由异常: {str(e)}", exc_info=True)
        return {'code':500,'msg':f'服务器内部错误: {str(e)}','current':False}