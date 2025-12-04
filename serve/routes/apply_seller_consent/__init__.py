import os
import shutil
from typing import Annotated

import aiomysql
from fastapi import APIRouter, Depends,Form, HTTPException

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import ApplySellerConsent
from services.management_token_verify import ManagementTokenVerify


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
                    mall_info = await execute_db_query(db,'select user,name,phone,describe_mall from shop_apply where user = %s',data.name)
                    if not sql_mall_info_data:
                        await execute_db_query(db,'insert into mall_info(user,mall_name,mall_phone,mall_descrine,mall_state) values(%s,%s,%s,%s,%s)',(mall_info[0][0],mall_info[0][1],mall_info[0][2],mall_info[0][3],1))
                        await execute_db_query(db,'update shop_apply set state = 3 where user = %s',data.name)
                        user_info = await execute_db_query(db,'select user,password from user where user = %s',data.name)
                        print(user_info)
                        print(data.name)
                        img = await execute_db_query(db,'select HeadPortrait from personal_details where user = %s',data.name)
                        print(img[0][0])
                        target_folder = "target_folder"
                        os.makedirs(target_folder, exist_ok=True)
                        target_path = os.path.join(target_folder, os.path.basename(img[0][0]))
                        shutil.copy2(img[0][0], target_path)
                        path_replaced = target_path.replace('\\', '/')
                        img = f"./{path_replaced}"
                        await execute_db_query(db,'insert into seller_sing(user,password,img) values(%s,%s,%s)',(user_info[0][0],user_info[0][1],img))
                        return {'msg':'同意成功','current':True}
                    else:
                        return {'msg':'数据库数据异常','current':False}

            else:
                    return {'msg':'验证失败','current':False}
        else:
            return {'msg':'验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))