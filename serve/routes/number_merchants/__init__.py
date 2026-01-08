import aiomysql
from fastapi import APIRouter,Depends,Form, HTTPException

from data.sql_client import get_db,execute_db_query
from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/number_merchants')
async def NumberMerchants(token:str=Form(min_length=6),
                          select:str=Form(default=None),
                          page:int=Form(default=1),db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    """
    获取商户数量列表
    支持通过店铺ID或卖家名字进行模糊搜索
    支持分页，每页5条数据
    """
    try:
        verify = ManagementTokenVerify(token=token,redis_client=redis_client)
        admin_tokrn_content = await verify.token_admin()
        if admin_tokrn_content['current']:
            data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
            verify_data = await verify.run(data)
            if verify_data['current']:
                cache = CacheService(redis_client)
                # 根据搜索关键词和页码生成缓存键
                if select and select.strip():
                    cache_key = cache._make_key('admin:merchant:list:search', select.strip(), page)
                else:
                    cache_key = cache._make_key('admin:merchant:list', page)
                
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
                        '''SELECT COUNT(DISTINCT u.user) 
                           FROM user u 
                           LEFT JOIN store s ON u.user = s.user 
                           WHERE u.merchant = 1 
                           AND (u.user LIKE %s OR (s.mall_id IS NOT NULL AND CAST(s.mall_id AS CHAR) LIKE %s))''',
                        (search_term, search_term))
                    # 获取分页数据
                    merchant = await execute_db_query(db,
                        '''SELECT DISTINCT u.user 
                           FROM user u 
                           LEFT JOIN store s ON u.user = s.user 
                           WHERE u.merchant = 1 
                           AND (u.user LIKE %s OR (s.mall_id IS NOT NULL AND CAST(s.mall_id AS CHAR) LIKE %s))
                           LIMIT %s OFFSET %s''',
                        (search_term, search_term, page_size, offset))
                else:
                    # 获取总数
                    total_count = await execute_db_query(db,'select count(*) from user where merchant = 1')
                    # 获取分页数据
                    merchant = await execute_db_query(db,
                        'SELECT user FROM user WHERE merchant = 1 LIMIT %s OFFSET %s',
                        (page_size, offset))
                
                total = total_count[0][0] if total_count else 0
                
                if not merchant:
                    result = {'merchant_list':[],'current':True,'page':total,'current_page':page}
                else:
                    merchant_list = [i[0] for i in merchant]
                    result = {'merchant_list':merchant_list,'current':True,'page':total,'current_page':page}
                
                # 搜索结果的缓存时间设置较短，避免搜索结果过期
                cache_expire = 60 if select and select.strip() else 300
                await cache.set(cache_key, result, expire=cache_expire)
                return result
            else:
                return {'msg':'不是管理员用户','current':False}
        else:
            return {'msg':'token验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))