import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form

from data.sql_client import get_db,execute_db_query
from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/get_apply_seller_list')
async def get_apply_seller_list(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    """
    管理员获取商户申请列表
    """
    try:
        verify = ManagementTokenVerify(token=token,redis_client=redis_client)
        admin_tokrn_content = await verify.token_admin()
        if admin_tokrn_content['current']:
            data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
            
            Verify_data = await verify.run(data)
            if Verify_data['current']:
                cache = CacheService(redis_client)
                cache_key = 'admin:apply:seller:list'
                cached_data = await cache.get(cache_key)
                if cached_data:
                    return cached_data
                
                sql_data = await execute_db_query(db,'select * from shop_apply where state = 1')
                page = await execute_db_query(db,'select count(*) from shop_apply where state = 1')
                if sql_data:
                    user_list = [list(i) for i in sql_data]
                    result = {'apply_list':user_list,'current':True,'page':page[0][0]}
                else:
                    result = {'apply_list':[],'current':True}
                await cache.set(cache_key, result, expire=120)
                return result
            else:
                return {'msg':'不是管理员用户','current':False}
        else:
            return {'msg':'token验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
