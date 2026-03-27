from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.data_mods import ManageCommodityClassifyEdit

router = APIRouter()


@router.post('/manage_commodity_classify_edit')
async def manage_commodity_classify_edit(data: Annotated[ManageCommodityClassifyEdit, Form()],
                                         db: Connection = Depends(get_db),
                                         redis: RedisClient = Depends(get_redis)):
    """平台端编辑商品分类"""
    async def execute():
        exist = await execute_db_query(db, 'SELECT id FROM classify WHERE id = %s', (data.classify_id,))
        if not exist:
            return {'current': False, 'msg': '分类不存在'}

        # 检查名称冲突（平台级分类 store_id IS NULL）
        name_check = await execute_db_query(db,
                                            'SELECT id FROM classify WHERE name = %s AND id != %s AND store_id IS NULL',
                                            (data.name, data.classify_id))
        if name_check:
            return {'current': False, 'msg': '分类名称已存在'}

        await execute_db_query(db,
                               'UPDATE classify SET name = %s WHERE id = %s',
                               (data.name, data.classify_id))

        cache = CacheService(redis)
        await cache.delete_pattern('admin:commodity:classify:*')
        return {'current': True, 'msg': '分类修改成功'}

    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, data.token, required="admin.commodity")
        if not ok:
            return {'current': False, 'msg': msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
