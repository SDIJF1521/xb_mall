from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form, HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.data_mods import ManageCommodityClassifyDelete

router = APIRouter()


@router.post('/manage_commodity_classify_delete')
async def manage_commodity_classify_delete(data: Annotated[ManageCommodityClassifyDelete, Form()],
                                           db: Connection = Depends(get_db),
                                           redis: RedisClient = Depends(get_redis)):
    """平台端删除商品分类"""
    verify = ManagementTokenVerify(token=data.token, redis_client=redis)
    admin_token_content = await verify.token_admin()

    async def execute():
        exist = await execute_db_query(db, 'SELECT id FROM classify WHERE id = %s', (data.classify_id,))
        if not exist:
            return {'current': False, 'msg': '分类不存在'}

        await execute_db_query(db, 'DELETE FROM classify WHERE id = %s', (data.classify_id,))

        cache = CacheService(redis)
        await cache.delete_pattern('admin:commodity:classify:*')
        await cache.delete_pattern('classify:*')
        return {'current': True, 'msg': '分类删除成功'}

    try:
        if admin_token_content['current']:
            sql_data = await execute_db_query(db, 'select user from manage_user where user = %s',
                                              admin_token_content['user'])
            Verify_data = await verify.run(sql_data)
            if Verify_data['current']:
                return await execute()
            else:
                return {'current': False, 'msg': '验证失败'}
        else:
            return {'current': False, 'msg': '验证失败'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
