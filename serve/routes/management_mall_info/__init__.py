import base64
from typing import Annotated

import aiomysql
from fastapi import APIRouter, Form, Depends, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.data_mods import ManagementGetMall

router = APIRouter()

@router.post('/management_mall_info')
async def MallInfo(data: Annotated[ManagementGetMall, Form()],
                   db: aiomysql.Connection = Depends(get_db),
                   redis_client: RedisClient = Depends(get_redis)):
    """
    管理员获取商户信息
    """
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis_client, data.token, required="admin.business"
        )
        if not ok:
            return {"current": False, "msg": msg}

        cache = CacheService(redis_client)
        cache_key = cache._make_key('admin:mall:info', data.name)
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        sql_mall_data = await execute_db_query(db, 'select * from mall_info where user = %s', data.name)
        if sql_mall_data:
            img = await execute_db_query(db, 'select HeadPortrait from personal_details where user = %s', data.name)

            try:
                if img:
                    with open(img[0][0], 'rb') as f:
                        mall_info = list(sql_mall_data[0])
                        mall_info.append(base64.b64encode(f.read()).decode('utf-8'))
                else:
                    with open('./img/通用/通用.png', 'rb') as f:
                        mall_info = list(sql_mall_data[0])
                        mall_info.append(base64.b64encode(f.read()).decode('utf-8'))
                result = {'msg': '获取成功', 'current': True, 'mall_info': mall_info}
                await cache.set(cache_key, result, expire=300)
                return result
            except:
                mall_info = list(sql_mall_data[0])
                mall_info.append('')
                result = {'msg': '获取成功', 'current': True, 'mall_info': mall_info}
                await cache.set(cache_key, result, expire=300)
                return result
        else:
            return {'msg': '该用户不为商家', 'current': False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
