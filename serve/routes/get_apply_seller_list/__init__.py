import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form

from data.sql_client import get_db,execute_db_query
from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/get_apply_seller_list')
async def get_apply_seller_list(token:str=Form(min_length=6), 
                                page:int=Form(default=1),
                                select:str=Form(default=None),
                                db:aiomysql.Connection = Depends(get_db),
                                redis_client=Depends(get_redis)):
    """
    管理员获取商户申请列表
    支持通过用户名或名称进行模糊搜索
    支持分页，每页5条数据
    """
    try:
        verify = ManagementTokenVerify(token=token,redis_client=redis_client)
        admin_tokrn_content = await verify.token_admin()
        if admin_tokrn_content['current']:
            data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
            
            Verify_data = await verify.run(data)
            if Verify_data['current']:
                cache = CacheService(redis_client)
                # 根据搜索关键词和页码生成缓存键
                if select and select.strip():
                    cache_key = cache._make_key('admin:apply:seller:list:search', select.strip(), page)
                else:
                    cache_key = cache._make_key('admin:apply:seller:list', page)
                
                cached_data = await cache.get(cache_key)
                if cached_data:
                    return cached_data
                
                # 分页参数
                page_size = 5
                offset = (page - 1) * page_size
                
                if select and select.strip():
                    search_term = f'%{select.strip()}%'
                    # 获取总数
                    total_count = await execute_db_query(db,
                        'SELECT COUNT(*) FROM shop_apply WHERE state = 1 AND (user LIKE %s OR name LIKE %s)',
                        (search_term, search_term))
                    # 获取分页数据
                    sql_data = await execute_db_query(db,
                        'SELECT * FROM shop_apply WHERE state = 1 AND (user LIKE %s OR name LIKE %s) LIMIT %s OFFSET %s',
                        (search_term, search_term, page_size, offset))
                else:
                    # 获取总数
                    total_count = await execute_db_query(db,'select count(*) from shop_apply where state = 1')
                    # 获取分页数据
                    sql_data = await execute_db_query(db,
                        'SELECT * FROM shop_apply WHERE state = 1 LIMIT %s OFFSET %s',
                        (page_size, offset))
                
                total = total_count[0][0] if total_count else 0
                
                if sql_data:
                    user_list = [list(i) for i in sql_data]
                    result = {'apply_list':user_list,'current':True,'page':total,'current_page':page}
                else:
                    result = {'apply_list':[],'current':True,'page':0,'current_page':page}
                
                # 搜索结果的缓存时间设置较短，避免搜索结果过期
                cache_expire = 60 if select and select.strip() else 120
                await cache.set(cache_key, result, expire=cache_expire)
                return result
            else:
                return {'msg':'不是管理员用户','current':False}
        else:
            return {'msg':'token验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
