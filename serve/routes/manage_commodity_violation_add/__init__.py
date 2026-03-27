from typing import Annotated
from datetime import datetime

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import ManageCommodityViolationAdd

router = APIRouter()


@router.post('/manage_commodity_violation_add')
async def manage_commodity_violation_add(data: Annotated[ManageCommodityViolationAdd, Form()],
                                         db: Connection = Depends(get_db),
                                         redis: RedisClient = Depends(get_redis),
                                         mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """平台端标记商品违规"""
    async def execute():
        sql_data = await execute_db_query(db,
                                          'SELECT * FROM shopping WHERE mall_id = %s AND shopping_id = %s',
                                          (data.mall_id, data.shopping_id))
        if not sql_data:
            return {'current': False, 'msg': '商品不存在'}

        await execute_db_query(db,
                               'UPDATE shopping SET audit = %s WHERE mall_id = %s AND shopping_id = %s',
                               (4, data.mall_id, data.shopping_id))
        await mongodb.update_one('shopping',
                                 {'shopping_id': data.shopping_id},
                                 {'$set': {'audit': 4}})

        await mongodb.insert_one('commodity_violation', {
            'mall_id': data.mall_id,
            'shopping_id': data.shopping_id,
            'reason': data.reason,
            'operator': username,
            'violation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        await mongodb.insert_one('commodity_msg', {
            'mall_id': data.mall_id,
            'shopping_id': data.shopping_id,
            'pass': 3,
            'msg': f'您的商品已被标记为违规，原因：{data.reason}',
            'auditor': username,
            'read': 0
        })

        cache = CacheService(redis)
        await cache.delete_pattern('admin:commodity:*')
        await cache.delete_pattern(f'commodity:list:{data.mall_id}:*')
        await cache.delete_pattern(f'commodity:inform:*')

        return {'current': True, 'msg': '已标记为违规商品'}

    try:
        ok, msg, username = await verify_admin_with_permission(db, redis, data.token, required="admin.commodity")
        if not ok:
            return {'current': False, 'msg': msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
