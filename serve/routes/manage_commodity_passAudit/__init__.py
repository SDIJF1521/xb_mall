from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.manage_admin_guard import verify_admin_with_permission
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
            

            await mongodb.insert_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id,'msg':msg_content,
                                        'pass':1,'auditor':username,'read':0})
            
            cache = CacheService(redis)
            await cache.delete_pattern('admin:commodity:apply:*')
            await cache.delete_pattern(f'commodity:inform:*')
            await cache.delete_pattern(f'commodity:list:{data.mall_id}:*')
            await cache.delete_pattern(f'commodity:search:{data.mall_id}:*')
            await cache.delete_pattern(f'admin:commodity:detail:{data.mall_id}:{data.shopping_id}')

            return {'msg':'审核通过','current':True}
        else:
            return {'msg':'审核失败','current':False}

    try:
        ok, msg, username = await verify_admin_with_permission(
            db, redis, data.token, required="admin.commodity_apply"
        )
        if not ok:
            return {"current": False, "msg": msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))