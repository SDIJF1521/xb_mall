import os
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.data_mods import DeleteMerchant
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.delete("/manage_merchant_delete")
async def manage_merchant_delete(data:Annotated[DeleteMerchant,Form()],
                                 db:Connection = Depends(get_db),
                                 redis:RedisClient=Depends(get_redis),
                                 mongodb:MongoDBClient=Depends(get_mongodb_client)):
    """管理员删除商户"""
    verify = ManagementTokenVerify(token=data.token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()

    async def execute():
        sql_data= await execute_db_query(db,'select * from mall_info where user = %s',(data.name))
        if sql_data:
            store_ids = await execute_db_query(db,'select mall_id from store where user = %s',(data.name))
            mall_id_list = [row[0] for row in store_ids] if store_ids else []
            
            cache = CacheService(redis)
            if mall_id_list:
                try:
                    deleted_shopping = await mongodb.delete_many('shopping', {'mall_id': {'$in': mall_id_list}})
                    deleted_msg = await mongodb.delete_many('commodity_msg', {'mall_id': {'$in': mall_id_list}})
                except Exception as e:
                    print(f"删除MongoDB数据时出错: {str(e)}")
            for mall_id in mall_id_list:
                img_path = f'./mall.img/{mall_id}.png'
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                    img_cache_key = cache._make_key('img_base64', img_path)
                    await cache.delete(img_cache_key)
                    await cache.delete(cache._make_key('mall_info', mall_id))
                    await cache.delete_pattern(f'commodity:list:{mall_id}:*')
                    await cache.delete_pattern(f'commodity:search:{mall_id}:*')
                    await cache.delete_pattern(f'commodity:inform:*')
                except:
                    pass
            await execute_db_query(db,"DELETE FROM mall_info WHERE user = %s",(data.name))
            await cache.delete_pattern(f'admin:merchant:*')
            await cache.delete_pattern(f'admin:apply:seller:*')
            await cache.delete_pattern(f'number:merchants')
            await cache.delete_pattern(f'admin:user:list')   
            await cache.delete_pattern(f'admin:mall:info:{data.user}')     
            await cache.delete(cache._make_key('user:data', data.name))
            await cache.delete(cache._make_key('user:apply:seller', data.name))
            await cache.delete_pattern(f'mall_name:user:{data.name}')
            for mall_id in mall_id_list:
                await cache.delete_pattern(f'mall_name:mall:{mall_id}')
            
            return {"code":200,"msg":"删除成功","success":True}
        else:
            return {"code":404,"msg":"用户不存在","success":False}
    try:    
        sql_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
        Verify_data = await verify.run(sql_data)
        if Verify_data['current']:
            return await execute()
        else:
            return {'current':False,'msg':'验证失败','code':401}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
