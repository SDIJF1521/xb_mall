import aiomysql
from fastapi import APIRouter,Depends,Form, HTTPException

from data.sql_client import get_db,execute_db_query
from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/number_merchants')
async def NumberMerchants(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    """
    获取商户数量列表
    """
    try:
        verify = ManagementTokenVerify(token=token,redis_client=redis_client)
        admin_tokrn_content = await verify.token_admin()
        if admin_tokrn_content['current']:
            data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
            verify_data = await verify.run(data)
            if verify_data['current']:
                cache = CacheService(redis_client)
                cache_key = 'admin:merchant:list'
                cached_data = await cache.get(cache_key)
                if cached_data:
                    return cached_data
                
                merchant = await execute_db_query(db,'select user from user where merchant = 1')
                page = await execute_db_query(db,'select count(*) from user where merchant = 1')
                if not merchant:
                    result = {'merchant_list':[],'current':True}
                else:
                    merchant_list = [i[0] for i in merchant]
                    result = {'merchant_list':merchant_list,'current':True,'page':page[0][0]}
                await cache.set(cache_key, result, expire=300)
                return result
            else:
                return {'msg':'不是管理员用户','current':False}
        else:
            return {'msg':'token验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))