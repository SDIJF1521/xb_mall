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
            sql_mall_info_data = await execute_db_query(db,'select * from mall_info where user = %s',admin_tokrn_content['user'])


            Verify_data = await verify.run(verify_data)
            if Verify_data['current']:
                    reject_user = await execute_db_query(db,'select user from rejection_reason where user = %s',data.name)
                    mall_id_list = await execute_db_query(db,'select mall_id from store')
                    if reject_user:
                         # 移除驳回内容
                         await execute_db_query(db,'DELETE FROM rejection_reason WHERE user = %s',data.name)
                    print(123)
                    mall_info = await execute_db_query(db,'select user,name,phone,describe_mall from shop_apply where user = %s',data.name)
                    print(mall_info)

                    if not sql_mall_info_data:
                        await execute_db_query(db,'insert into mall_info(user,mall_name,mall_phone,mall_descrine,mall_state) values(%s,%s,%s,%s,%s)',(mall_info[0][0],mall_info[0][1],mall_info[0][2],mall_info[0][3],1))


                        await execute_db_query(db,'update shop_apply set state = 3 where user = %s',data.name)
                        return {'msg':'同意成功','current':True}
                    else:
                        return {'msg':'数据库数据异常','current':False}

            else:
                    return {'msg':'验证失败','current':False}
        else:
            return {'msg':'验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))