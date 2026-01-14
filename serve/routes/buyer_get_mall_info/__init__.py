import os
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Form,Depends

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService
from data.file_client import read_file_base64_with_cache

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import GetMallInfo


router = APIRouter()

@router.post("/buyer_get_mall_info")
async def buyer_get_mall_info(data:Annotated[GetMallInfo,Form()],db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):
    """获取店铺信息"""
    try:
        verify_duter_token = VerifyDuterToken(data.token,redis)
        token_data = await verify_duter_token.token_data()
        
        # 检查token是否有效
        if not token_data:
            return {"code":400,"msg":"token无效或已过期","data":None,'current':False}

        async def execute(mall_id:int=None):
            cache = CacheService(redis)
            
            # 确定查询的店铺ID和缓存键
            query_mall_id = data.id if data.id is not None else mall_id
            
            if data.id is not None:
                cache_key = cache._make_key('mall_info', data.id)
                bloom_item_id = f"mall:{data.id}"
            elif mall_id is not None:
                cache_key = cache._make_key('mall_info', mall_id)
                bloom_item_id = f"mall:{mall_id}"
            else:
                cache_key = cache._make_key('mall_info:user', token_data.get("user"))
                bloom_item_id = f"mall:user:{token_data.get('user')}"
            

            async def fetch_mall_info():
                if data.id is None and mall_id is None:
                    sql_mall_info = await execute_db_query(db,"select * from store where user = %s",(token_data.get("user")))
                elif data.id is not None:
                    sql_mall_info = await execute_db_query(db,"select * from store where mall_id = %s",(data.id))
                else:
                     sql_mall_info = await execute_db_query(db,"select * from store where mall_id = %s",(mall_id))
                
                rtn = []
                if sql_mall_info:
                    rtn = [{"id":i[0],"user":i[1],"mall_name":i[2],"phone":i[3],"site":i[4],"info":i[5],"img":i[6],"time":i[7],'state':i[8],'state_platform':i[9]}for i in sql_mall_info]
                    import asyncio
                    img_tasks = [
                        read_file_base64_with_cache(i.get('img', ''), redis, cache_expire=3600)
                        for i in rtn
                    ]
                    img_results = await asyncio.gather(*img_tasks)
                    for i, encoded_string in zip(rtn, img_results):
                        i['img'] = encoded_string
                
                if rtn:
                    return {"code":200,"msg":"success","data":rtn,'current':True}
                return None
            
            if query_mall_id is not None:
                result = await cache.get_or_set_with_bloom(
                    key=cache_key,
                    item_id=bloom_item_id,
                    func=fetch_mall_info,
                    expire=300,
                    return_none_if_not_exists=True
                )
                if result:
                    return result
                return {"code":404,"msg":"店铺不存在","data":None,'current':False}
            else:
                cached_data = await cache.get(cache_key)
                if cached_data:
                    return cached_data
                result = await fetch_mall_info()
                if result:
                    await cache.set(cache_key, result, expire=300)
                    return result
                return {"code":404,"msg":"未找到店铺信息","data":None,'current':False}

        station = token_data.get('station')
        if station == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data and len(verify_data) > 0 and verify_data[0]:
                return await execute()
            else:
                return {"code":400,"msg":"token verify failed","data":None,'current':False}
        elif station == '2':
            if not token_data.get('mall_id') or not token_data.get('role'):
                return {"code":400,"msg":"token信息不完整","data":None,'current':False}
            
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            if not role_authority or len(role_authority) == 0 or len(role_authority[0]) == 0:
                return {"code":400,"msg":"权限验证失败","data":None,'current':False}
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            if execute_code and len(execute_code) > 2 and execute_code[2]:
                return await execute(token_data.get('mall_id'))
            else:
                return {"code":400,"msg":"权限不足，无法查询店铺信息","data":None,'current':False}
        else:
            return {"code":400,"msg":"无效的用户类型","data":None,'current':False}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"buyer_get_mall_info 路由异常: {str(e)}", exc_info=True)
        return {"code":500,"msg":f"服务器内部错误: {str(e)}","data":None,'current':False}