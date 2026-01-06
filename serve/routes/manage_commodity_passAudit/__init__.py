from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.data_mods import ManageCommodityPassAudit
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.post('/manage_commodity_passAudit')
async def manage_commodity_passAudit(data:Annotated[ManageCommodityPassAudit,Form(...)],
                                     db:Connection=Depends(get_db),
                                     redis:RedisClient = Depends(get_redis),
                                     mongodb:MongoDBClient = Depends(get_mongodb_client)):
    """
    管理员审核商品通过
    """
    verify = ManagementTokenVerify(token=data.token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()
    
    async def execute():
        """执行审核通过的核心逻辑"""
        sql_commodity_data = await execute_db_query(db,
                                                    'select * from shopping where mall_id = %s and shopping_id = %s',
                                                    (data.mall_id,data.shopping_id))
        if sql_commodity_data:
            await execute_db_query(db,
                                   'update shopping set audit = %s where mall_id = %s and shopping_id = %s',
                                   (1,data.mall_id,data.shopping_id))
            await mongodb.update_one('shopping',{'shopping_id':data.shopping_id},
                                    {'$set':{'audit':1}})
            
            mongodb_commodity_data = await mongodb.find_one('shopping',{'mall_id':data.mall_id,'shopping_id':data.shopping_id})
            mongodb_sql = await mongodb.find_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id})
            commodity_name = mongodb_commodity_data.get('name', '未知商品')
            
            if not data.remark is None:
                msg_content = f'商品 {commodity_name} 审核通过，审核备注：\n无'
            else:
                msg_content = f'商品 {commodity_name} 审核通过，审核备注：\n{data.remark}'
            
            if mongodb_sql:
                await mongodb.update_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id},
                                        {'$set':{'msg':msg_content,
                                        'pass':1,'auditor':admin_tokrn_content['user']}})
            else:
                await mongodb.insert_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id,'msg':msg_content,
                                        'pass':1,'auditor':admin_tokrn_content['user']})
            
            cache = CacheService(redis)
            await cache.delete_pattern('admin:commodity:apply:*')
            await cache.delete_pattern(f'commodity:inform:*')
            await cache.delete_pattern(f'commodity:list:{data.mall_id}:*')
            await cache.delete_pattern(f'commodity:search:{data.mall_id}:*')
            await cache.delete_pattern(f'admin:commodity:detail:{data.mall_id}:{data.shopping_id}')

            return {'msg':'审核通过','current':True}
        else:
            return {'msg':'审核失败','current':False}
    
    sql_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
    verify_data = await verify.run(sql_data)
    if verify_data['current']:
        return await execute()
    else:
        return {'msg':'验证失败','current':False}