import aiomysql
from fastapi import APIRouter, Depends, Form, HTTPException

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

router = APIRouter()

@router.post('/number_merchants')
async def NumberMerchants(token: str = Form(min_length=6),
                          select: str = Form(default=None),
                          page: int = Form(default=1),
                          db: aiomysql.Connection = Depends(get_db),
                          redis_client: RedisClient = Depends(get_redis)):
    """
    获取商户数量列表
    支持通过店铺ID或卖家名字进行模糊搜索
    支持分页，每页5条数据
    """
    try:
        ok, msg, _ = await verify_admin_with_permission(db, redis_client, token, required="admin.user.merchant")
        if not ok:
            return {"current": False, "msg": msg}

        cache = CacheService(redis_client)
        if select and select.strip():
            cache_key = cache._make_key('admin:merchant:list:search', select.strip(), page)
        else:
            cache_key = cache._make_key('admin:merchant:list', page)
        
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        page_size = 5
        offset = (page - 1) * page_size
        
        if select and select.strip():
            search_term = f'%{select.strip()}%'
            total_count = await execute_db_query(db,
                '''SELECT COUNT(DISTINCT u.user) 
                   FROM user u 
                   LEFT JOIN store s ON u.user = s.user 
                   WHERE u.merchant = 1 
                   AND (u.user LIKE %s OR (s.mall_id IS NOT NULL AND CAST(s.mall_id AS CHAR) LIKE %s))''',
                (search_term, search_term))
            merchant = await execute_db_query(db,
                '''SELECT DISTINCT u.user 
                   FROM user u 
                   LEFT JOIN store s ON u.user = s.user 
                   WHERE u.merchant = 1 
                   AND (u.user LIKE %s OR (s.mall_id IS NOT NULL AND CAST(s.mall_id AS CHAR) LIKE %s))
                   LIMIT %s OFFSET %s''',
                (search_term, search_term, page_size, offset))
        else:
            total_count = await execute_db_query(db, 'select count(*) from user where merchant = 1')
            merchant = await execute_db_query(db,
                'SELECT user FROM user WHERE merchant = 1 LIMIT %s OFFSET %s',
                (page_size, offset))
        
        total = total_count[0][0] if total_count else 0
        
        if not merchant:
            result = {'merchant_list': [], 'current': True, 'page': total, 'current_page': page}
        else:
            merchant_list = [i[0] for i in merchant]
            result = {'merchant_list': merchant_list, 'current': True, 'page': total, 'current_page': page}
        
        cache_expire = 60 if select and select.strip() else 300
        await cache.set(cache_key, result, expire=cache_expire)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
