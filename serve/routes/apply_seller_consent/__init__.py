import os
import shutil
from typing import Annotated

import aiomysql
from fastapi import APIRouter, Depends,Form, HTTPException

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import ApplySellerConsent
from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService


router = APIRouter()

@router.post('/apply_seller_consent')
async def apply_seller_consent(data:Annotated[ApplySellerConsent,Form()], db:aiomysql.Connection = Depends(get_db),redis_client:RedisClient=Depends(get_redis)):
    """管理员同意商户申请"""
    try:
        verify = ManagementTokenVerify(token=data.token,redis_client=redis_client)
        admin_tokrn_content = await verify.token_admin()
        if admin_tokrn_content['current']:
            verify_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
            sql_mall_info_data = await execute_db_query(db,'select * from mall_info where user = %s',admin_tokrn_content['user'])

            Verify_data = await verify.run(verify_data)
            if Verify_data['current']:
                reject_user = await execute_db_query(db,'select user from rejection_reason where user = %s',data.name)
                if reject_user:
                    await execute_db_query(db,'DELETE FROM rejection_reason WHERE user = %s',data.name)
                
                mall_info = await execute_db_query(db,'select user,name,phone,describe_mall from shop_apply where user = %s',data.name)
                if not sql_mall_info_data:
                    await execute_db_query(db,'insert into mall_info(user,mall_name,mall_phone,mall_descrine,mall_state) values(%s,%s,%s,%s,%s)',(mall_info[0][0],mall_info[0][1],mall_info[0][2],mall_info[0][3],1))
                    await execute_db_query(db,'update shop_apply set state = 3 where user = %s',data.name)
                    
                    user_info = await execute_db_query(db,'select user,password from user where user = %s',data.name)
                    img_query = await execute_db_query(db,'select HeadPortrait from personal_details where user = %s',data.name)
                    if img_query and img_query[0][0]:
                        source_img_path = img_query[0][0]
                        target_folder = "target_folder"
                        os.makedirs(target_folder, exist_ok=True)
                        target_path = os.path.join(target_folder, os.path.basename(source_img_path))
                        shutil.copy2(source_img_path, target_path)
                        path_replaced = target_path.replace('\\', '/')
                        img = f"./{path_replaced}"
                        await execute_db_query(db,'insert into seller_sing(user,password,img) values(%s,%s,%s)',(user_info[0][0],user_info[0][1],img))
                        
                        cache = CacheService(redis_client)
                        if os.path.exists(source_img_path):
                            source_img_cache_key = cache._make_key('img_base64', source_img_path)
                            await cache.delete(source_img_cache_key)
                        if os.path.exists(target_path):
                            target_img_cache_key = cache._make_key('img_base64', target_path)
                            await cache.delete(target_img_cache_key)
                    else:
                        await execute_db_query(db,'insert into seller_sing(user,password,img) values(%s,%s,%s)',(user_info[0][0],user_info[0][1],None))
                        cache = CacheService(redis_client)
                    
                    await cache.delete('admin:apply:seller:list')
                    await cache.delete(cache._make_key('user:apply:seller', data.name))
                    await cache.delete_pattern('admin:merchant:*')
                    await cache.delete_pattern('number:merchants')
                    await cache.delete_pattern('admin:user:list')
                    
                    return {'msg':'同意成功','current':True}
                else:
                    return {'msg':'数据库数据异常','current':False}

            else:
                return {'msg':'验证失败','current':False}
        else:
            return {'msg':'验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))