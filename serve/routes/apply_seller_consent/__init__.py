from typing import Annotated

import aiomysql
from fastapi import APIRouter, Depends,Form, HTTPException

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient
from data.data_mods import ApplySellerConsent
from services.management_token_verify import ManagementTokenVerify

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()
@router.post('/apply_seller_consent')
async def apply_seller_consent(data:Annotated[ApplySellerConsent,Form()], db:aiomysql.Connection = Depends(get_db),redis_client:RedisClient=Depends(get_redis)):
    try:
        verify = ManagementTokenVerify(token=data.token,redis_client=redis_client)
        admin_tokrn_content = await verify.token_admin()
        if admin_tokrn_content['current']:
            verify_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])

            Verify_data = await verify.run(verify_data)
            if Verify_data['current']:
                    print(f'yes1{data.name}')
                    await execute_db_query(db,'update user set merchant = 1 where user = %s',data.name)
                    await execute_db_query(db,'update shop_apply set state = 3 where user = %s',data.name)
                    return {'msg':'同意成功','current':True}
            else:
                    return {'msg':'验证失败','current':False}
        else:
            return {'msg':'验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))