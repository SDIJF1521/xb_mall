from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.data_mods import ManageCommodityClassifyQuery

router = APIRouter()


@router.get('/manage_commodity_classify_list')
async def manage_commodity_classify_list(data: ManageCommodityClassifyQuery = Depends(),
                                         access_token: str = Header(...),
                                         db: Connection = Depends(get_db),
                                         redis: RedisClient = Depends(get_redis)):
    """平台端获取商品分类列表"""
    verify = ManagementTokenVerify(token=access_token, redis_client=redis)
    admin_token_content = await verify.token_admin()

    async def execute():
        cache = CacheService(redis)
        page_size = data.page_size
        page = data.page if data.page and data.page > 0 else 1
        offset = (page - 1) * page_size

        cache_key = cache._make_key('admin:commodity:classify', page, page_size, data.select_data or '')
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data

        if data.select_data and data.select_data.strip():
            count_sql = 'SELECT COUNT(*) FROM classify WHERE name LIKE %s'
            list_sql = 'SELECT c.id, c.name, c.store_id, s.mall_name FROM classify c LEFT JOIN store s ON c.store_id = s.mall_id WHERE c.name LIKE %s ORDER BY c.id DESC LIMIT %s OFFSET %s'
            keyword = f'%{data.select_data.strip()}%'
            total_data = await execute_db_query(db, count_sql, (keyword,))
            classify_data = await execute_db_query(db, list_sql, (keyword, page_size, offset))
        else:
            count_sql = 'SELECT COUNT(*) FROM classify'
            list_sql = 'SELECT c.id, c.name, c.store_id, s.mall_name FROM classify c LEFT JOIN store s ON c.store_id = s.mall_id ORDER BY c.id DESC LIMIT %s OFFSET %s'
            total_data = await execute_db_query(db, count_sql)
            classify_data = await execute_db_query(db, list_sql, (page_size, offset))

        total = total_data[0][0] if total_data and total_data[0] else 0
        out = []
        if classify_data:
            for row in classify_data:
                out.append({
                    'id': row[0],
                    'name': row[1],
                    'store_id': row[2],
                    'mall_name': row[3] if row[3] else '平台分类',
                })

        result = {'current': True, 'classify_list': out, 'total': total, 'page': page, 'page_size': page_size}
        await cache.set(cache_key, result, expire=60)
        return result

    try:
        sql_data = await execute_db_query(db, 'select user from manage_user where user = %s',
                                          admin_token_content['user'])
        Verify_data = await verify.run(sql_data)
        if Verify_data['current']:
            return await execute()
        else:
            return {'current': False, 'msg': '验证失败', 'code': 401}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
