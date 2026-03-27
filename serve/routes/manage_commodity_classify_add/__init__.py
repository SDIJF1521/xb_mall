from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.data_mods import ManageCommodityClassifyAdd

router = APIRouter()


@router.post('/manage_commodity_classify_add')
async def manage_commodity_classify_add(data: Annotated[ManageCommodityClassifyAdd, Form()],
                                        db: Connection = Depends(get_db),
                                        redis: RedisClient = Depends(get_redis)):
    """平台端新增商品分类（平台级分类，store_id 为 NULL）"""
    async def execute():
        # 检查是否已存在同名平台分类（store_id IS NULL 表示平台级）
        exist = await execute_db_query(db,
                                       'SELECT id FROM classify WHERE name = %s AND store_id IS NULL',
                                       (data.name,))
        if exist:
            return {'current': False, 'msg': '该分类名称已存在'}

        # 获取最大 id 并 +1（classify 表 id 需显式填写）
        max_row = await execute_db_query(db, 'SELECT IFNULL(MAX(id), 0) FROM classify')
        next_id = int(max_row[0][0]) + 1

        await execute_db_query(db,
                               'INSERT INTO classify (id, name, store_id) VALUES (%s, %s, NULL)',
                               (next_id, data.name))

        cache = CacheService(redis)
        await cache.delete_pattern('admin:commodity:classify:*')
        await cache.delete_pattern('classify:*')
        return {'current': True, 'msg': '分类添加成功'}

    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, data.token, required="admin.commodity")
        if not ok:
            return {'current': False, 'msg': msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
