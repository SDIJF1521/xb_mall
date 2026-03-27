from typing import Annotated

from aiomysql import connect
from fastapi import APIRouter,Depends,Form,HTTPException
from starlette.responses import Content

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.data_mods import ManageRejectCommodityApply
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.post('/manage_commodity_rejectAudit')
async def manage_commodity_rejectAudit(data:Annotated[ManageRejectCommodityApply,Form()],
                                        db:Content = Depends(get_db),
                                        redis:RedisClient = Depends(get_redis),
                                        mongodb:MongoDBClient = Depends(get_mongodb_client)):
    """管理员驳回商品上架申请"""
    async def execute():
        sql_data = await execute_db_query(db,
                                          'select * from shopping where mall_id= %s and shopping_id = %s',
                                          (data.mall_id,data.shopping_id))
        if sql_data:
            await execute_db_query(db,
                                   'update shopping set audit = %s where mall_id = %s and shopping_id = %s',
                                   (2,data.mall_id,data.shopping_id))
            await mongodb.update_one('shopping',{'shopping_id':data.shopping_id}, {'$set': {'audit': 2}})
            
            mongodb_data_msg = await mongodb.find_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id,'pass':0,'auditor':username})

            await mongodb.insert_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id,'pass':0,'msg':data.reason,'auditor':username,'read':0})
            
            cache = CacheService(redis)
            await cache.delete_pattern('admin:commodity:apply:*')
            await cache.delete_pattern(f'commodity:inform:*')
            await cache.delete_pattern(f'commodity:list:{data.mall_id}:*')
            await cache.delete_pattern(f'commodity:search:{data.mall_id}:*')
            await cache.delete_pattern(f'admin:commodity:detail:{data.mall_id}:{data.shopping_id}')
            
            return {'msg':'拒绝成功','current':True}
        else:
            return {'msg':'商品不存在','current':False}

    try:
        ok, msg, username = await verify_admin_with_permission(
            db, redis, data.token, required="admin.commodity_apply"
        )
        if not ok:
            return {"current": False, "msg": msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))