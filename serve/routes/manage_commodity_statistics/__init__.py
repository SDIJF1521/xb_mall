from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()


@router.get('/manage_commodity_statistics')
async def manage_commodity_statistics(access_token: str = Header(...),
                                      db: Connection = Depends(get_db),
                                      redis: RedisClient = Depends(get_redis),
                                      mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """平台端获取商品统计数据"""
    async def execute():
        cache = CacheService(redis)
        cache_key = 'admin:commodity:statistics'
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data

        # 各状态商品数量统计
        total_count = await mongodb.count_documents('shopping', {})
        on_sale_count = await mongodb.count_documents('shopping', {'audit': 1})
        off_shelf_count = await mongodb.count_documents('shopping', {'audit': 3})
        auditing_count = await mongodb.count_documents('shopping', {'audit': 0})
        rejected_count = await mongodb.count_documents('shopping', {'audit': 2})
        violation_count = await mongodb.count_documents('shopping', {'audit': 4})

        # 各店铺商品数量分布（前10）
        store_distribution = await mongodb.aggregate('shopping', [
            {'$group': {'_id': '$mall_id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ])
        store_dist_out = []
        if store_distribution:
            mall_ids = [item['_id'] for item in store_distribution if item['_id'] is not None]
            mall_names = {}
            if mall_ids:
                placeholders = ','.join(['%s'] * len(mall_ids))
                sql = f'SELECT mall_id, mall_name FROM store WHERE mall_id IN ({placeholders})'
                store_data = await execute_db_query(db, sql, tuple(mall_ids))
                if store_data:
                    for row in store_data:
                        mall_names[row[0]] = row[1]

            for item in store_distribution:
                store_dist_out.append({
                    'mall_id': item['_id'],
                    'mall_name': mall_names.get(item['_id'], '未知店铺'),
                    'count': item['count']
                })

        # 各分类商品数量分布
        classify_data = await execute_db_query(db,
            '''SELECT c.id, c.name, COUNT(s.shopping_id) as cnt
               FROM classify c
               LEFT JOIN shopping s ON s.classify_categorize = c.id
               GROUP BY c.id, c.name
               ORDER BY cnt DESC
               LIMIT 10''')
        classify_dist_out = []
        if classify_data:
            for row in classify_data:
                classify_dist_out.append({
                    'classify_id': row[0],
                    'name': row[1],
                    'count': row[2]
                })

        # 近7天新增商品趋势
        trend_data = await execute_db_query(db,
            '''SELECT DATE(time) as dt, COUNT(*) as cnt
               FROM shopping
               WHERE time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
               GROUP BY DATE(time)
               ORDER BY dt ASC''')
        trend_out = []
        if trend_data:
            for row in trend_data:
                trend_out.append({
                    'date': row[0].strftime('%Y-%m-%d') if hasattr(row[0], 'strftime') else str(row[0]),
                    'count': row[1]
                })

        result = {
            'current': True,
            'statistics': {
                'total': total_count,
                'on_sale': on_sale_count,
                'off_shelf': off_shelf_count,
                'auditing': auditing_count,
                'rejected': rejected_count,
                'violation': violation_count,
            },
            'store_distribution': store_dist_out,
            'classify_distribution': classify_dist_out,
            'trend': trend_out
        }

        await cache.set(cache_key, result, expire=120)
        return result

    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis, access_token, required="admin.commodity")
        if not ok:
            return {'current': False, 'msg': msg}
        return await execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
