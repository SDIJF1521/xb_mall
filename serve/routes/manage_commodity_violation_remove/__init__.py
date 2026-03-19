from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form, HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.data_mods import ManageCommodityViolationRemove

router = APIRouter()


@router.post('/manage_commodity_violation_remove')
async def manage_commodity_violation_remove(data: Annotated[ManageCommodityViolationRemove, Form()],
                                            db: Connection = Depends(get_db),
                                            redis: RedisClient = Depends(get_redis),
                                            mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """平台端取消商品违规标记（恢复为已下架状态）"""
    verify = ManagementTokenVerify(token=data.token, redis_client=redis)
    admin_token_content = await verify.token_admin()

    async def execute():
        sql_data = await execute_db_query(db,
                                          'SELECT * FROM shopping WHERE mall_id = %s AND shopping_id = %s',
                                          (data.mall_id, data.shopping_id))
        if not sql_data:
            return {'current': False, 'msg': '商品不存在'}

        await execute_db_query(db,
                               'UPDATE shopping SET audit = %s WHERE mall_id = %s AND shopping_id = %s',
                               (3, data.mall_id, data.shopping_id))
        await mongodb.update_one('shopping',
                                 {'shopping_id': data.shopping_id},
                                 {'$set': {'audit': 3}})

        await mongodb.delete_one('commodity_violation', {
            'mall_id': data.mall_id,
            'shopping_id': data.shopping_id
        })

        await mongodb.insert_one('commodity_msg', {
            'mall_id': data.mall_id,
            'shopping_id': data.shopping_id,
            'pass': 4,
            'msg': '您的商品违规标记已被取消，当前状态为已下架，您可以重新上架',
            'auditor': admin_token_content['user'],
            'read': 0
        })

        cache = CacheService(redis)
        await cache.delete_pattern('admin:commodity:*')
        await cache.delete_pattern(f'commodity:list:{data.mall_id}:*')
        await cache.delete_pattern(f'commodity:inform:*')

        return {'current': True, 'msg': '已取消违规标记'}

    try:
        if admin_token_content['current']:
            verify_data = await execute_db_query(db, 'select user from manage_user where user = %s',
                                                 admin_token_content['user'])
            Verify_data = await verify.run(verify_data)
            if Verify_data['current']:
                return await execute()
            else:
                return {'current': False, 'msg': '验证失败'}
        else:
            return {'current': False, 'msg': '验证失败'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
