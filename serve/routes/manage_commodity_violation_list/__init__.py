from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.file_client import read_file_base64_with_cache
from data.data_mods import ManageCommodityViolationQuery

router = APIRouter()


@router.get('/manage_commodity_violation_list')
async def manage_commodity_violation_list(data: ManageCommodityViolationQuery = Depends(),
                                          access_token: str = Header(...),
                                          db: Connection = Depends(get_db),
                                          redis: RedisClient = Depends(get_redis),
                                          mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """平台端获取违规商品列表"""
    async def execute():
        cache = CacheService(redis)
        page_size = data.page_size
        page = data.page if data.page and data.page > 0 else 1
        offset = (page - 1) * page_size

        cache_key = cache._make_key('admin:commodity:violation', page, page_size, data.select_data or '')
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data

        # 查询违规商品（audit=4 标记为违规）
        query = {'audit': 4}
        if data.select_data and data.select_data.strip():
            query['name'] = {'$regex': data.select_data.strip(), '$options': 'i'}

        total = await mongodb.count_documents('shopping', query)
        mongodb_data = await mongodb.find_many('shopping', query,
                                               limit=page_size,
                                               skip=offset,
                                               sort=[('time', -1)])

        out = []
        if mongodb_data:
            mall_ids = list(set(item['mall_id'] for item in mongodb_data))
            mall_names = {}
            if mall_ids:
                placeholders = ','.join(['%s'] * len(mall_ids))
                sql = f'SELECT mall_id, mall_name FROM store WHERE mall_id IN ({placeholders})'
                store_data = await execute_db_query(db, sql, tuple(mall_ids))
                if store_data:
                    for row in store_data:
                        mall_names[row[0]] = row[1]

            for item in mongodb_data:
                violation_info = await mongodb.find_one('commodity_violation', {
                    'mall_id': item.get('mall_id'),
                    'shopping_id': item.get('shopping_id')
                })
                img_path = item.get('img_list', [''])[0] if item.get('img_list') else ''
                img = ''
                if img_path:
                    img_b64 = await read_file_base64_with_cache(img_path, redis, cache_expire=3600)
                    if img_b64:
                        img = f'data:image/jpeg;base64,{img_b64}'
                out.append({
                    'mall_id': item.get('mall_id'),
                    'shopping_id': item.get('shopping_id'),
                    'name': item.get('name', ''),
                    'info': item.get('info', ''),
                    'time': item.get('time', ''),
                    'mall_name': mall_names.get(item.get('mall_id'), '未知店铺'),
                    'reason': violation_info.get('reason', '') if violation_info else '',
                    'violation_time': violation_info.get('violation_time', '') if violation_info else '',
                    'img': img,
                })

        result = {'current': True, 'violation_list': out, 'total': total, 'page': page, 'page_size': page_size}
        await cache.set(cache_key, result, expire=30)
        return result

    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, access_token, required="admin.commodity")
        if not ok:
            return {'current': False, 'msg': msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
