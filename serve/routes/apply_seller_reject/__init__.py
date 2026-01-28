from typing import Annotated

import aiomysql
from fastapi import APIRouter, Depends, Form, HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService
from data.data_mods import ApplySellerReject
from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db, execute_db_query


router = APIRouter()

@router.post('/apply_seller_reject')
async def apply_seller_reject(data:Annotated[ApplySellerReject,Form()], db:aiomysql.Connection = Depends(get_db),redis_client:RedisClient=Depends(get_redis)):
    """
    管理员驳回商户申请
    """
    try:
        verify = ManagementTokenVerify(token=data.token,redis_client=redis_client)
        admin_tokrn_content = await verify.token_admin()
        if admin_tokrn_content['current']:
            verify_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])

            Verify_data = await verify.run(verify_data)
            if Verify_data['current']:
                reject_user_list = await execute_db_query(db,'select user from rejection_reason where user = %s',data.name)
                cache = CacheService(redis_client)
                if reject_user_list:
                    await execute_db_query(db,'update rejection_reason set reason=%s where user = %s',(data.reason,data.name))
                    await execute_db_query(db,'update shop_apply set state=%s where user = %s',(2,data.name))
                else:
                    await execute_db_query(db,'update shop_apply set state=%s where user = %s',(2,data.name))
                    await execute_db_query(db,'insert into rejection_reason(user,reason) values(%s,%s)',(data.name,data.reason))
                
                await cache.delete_pattern('admin:apply:seller:list:*')
                await cache.delete_pattern('admin:apply:seller:search:%s' % data.name)
                await cache.delete_pattern(cache._make_key('user:apply:seller', data.name))
            
                
                return {'msg':'拒绝成功','current':True}
            else:
                return {'msg':'验证失败','current':False}
        else:
            return {'msg':'验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
