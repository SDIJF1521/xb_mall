import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient, get_redis
from services.manage_admin_guard import verify_admin_with_permission
from services.cache_service import CacheService

router = APIRouter()

@router.post('/get_apply_seller_list')
async def get_apply_seller_list(token:str=Form(min_length=6), 
                                page:int=Form(default=1),
                                select:str=Form(default=None),
                                db:aiomysql.Connection = Depends(get_db),
                                redis_client:RedisClient=Depends(get_redis)):
    """
    管理员获取商户申请列表
    支持通过用户名或名称进行模糊搜索
    支持分页，每页5条数据
    """
    try:
        ok, msg, _ = await verify_admin_with_permission(
            db, redis_client, token, required="admin.audit_seller"
        )
        if not ok:
            return {"current": False, "msg": msg}

        cache = CacheService(redis_client)
        if select and select.strip():
            cache_key = cache._make_key('admin:apply:seller:list:search', select.strip(), page)
        else:
            cache_key = cache._make_key('admin:apply:seller:list', page)
        
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        page_size = 5
        offset = (page - 1) * page_size
        
        if select and select.strip():
            search_term = f'%{select.strip()}%'
            total_count = await execute_db_query(db,
                'SELECT COUNT(*) FROM shop_apply WHERE state = 1 AND (user LIKE %s OR name LIKE %s)',
                (search_term, search_term))
            sql_data = await execute_db_query(db,
                'SELECT * FROM shop_apply WHERE state = 1 AND (user LIKE %s OR name LIKE %s) LIMIT %s OFFSET %s',
                (search_term, search_term, page_size, offset))
        else:
            total_count = await execute_db_query(db,'select count(*) from shop_apply where state = 1')
            sql_data = await execute_db_query(db,
                'SELECT * FROM shop_apply WHERE state = 1 LIMIT %s OFFSET %s',
                (page_size, offset))
        
        total = total_count[0][0] if total_count else 0
        
        if sql_data:
            user_list = [list(i) for i in sql_data]
            result = {'apply_list':user_list,'current':True,'page':total,'current_page':page}
        else:
            result = {'apply_list':[],'current':True,'page':0,'current_page':page}
        
        cache_expire = 60 if select and select.strip() else 120
        await cache.set(cache_key, result, expire=cache_expire)
        return result
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
