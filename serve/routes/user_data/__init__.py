import aiomysql
import logging

from fastapi import APIRouter,Depends,Form,HTTPException

from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient
from services.user_info import UserInfo
from services.cache_service import CacheService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post('/user_data')
async def user_data(token:str = Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """获取用户基础数据"""
    try:
        user_info = UserInfo(token)
        user_info_data = await user_info.token_analysis()
        
        if not user_info_data.get('current'):
            return {'msg': user_info_data.get('msg', 'token无效'), 'current': False}
        
        cache = CacheService(redis)
        cache_key = cache._make_key('user:data', user_info_data['user'])
        
        # 先检查缓存
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # 查询数据库
        try:
            user_data = await execute_db_query(db,'select user, email, merchant, time from user where user = %s', (user_info_data['user'],))
        except Exception as e:
            logger.error(f"数据库查询失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f'数据库查询失败: {str(e)}')
        
        # 检查查询结果
        if not user_data or len(user_data) == 0:
            # 用户不存在，使用布隆过滤器防止缓存穿透
            bloom_item_id = f"user:{user_info_data['user']}"
            try:
                exists = await cache.bloom_filter.exists(bloom_item_id)
                if not exists:
                    await cache.bloom_filter.add(bloom_item_id)
            except Exception as e:
                # 布隆过滤器操作失败，记录日志但不影响主流程
                logger.warning(f"布隆过滤器操作失败: {str(e)}")
            return {'msg':'用户不存在','current':False}
        
        # 处理查询结果
        row = user_data[0]
        if len(row) >= 4:
            # 返回用户基础数据：用户名和merchant字段（0=买家，1=卖家）
            # data[0] = 用户名, data[1] = merchant
            result = {'msg':'查询成功','current':True,'data':[row[0], row[2]]}
        elif len(row) >= 3:
            # 如果只有3列，返回用户名和merchant
            result = {'msg':'查询成功','current':True,'data':[row[0], row[2]]}
        else:
            # 如果列数不足，至少返回用户名，merchant默认为0（买家）
            result = {'msg':'查询成功','current':True,'data':[row[0], 0]}
        
        # 缓存结果
        try:
            await cache.set(cache_key, result, expire=300)
            # 添加到布隆过滤器（用户存在）
            await cache.bloom_filter.add(f"user:{user_info_data['user']}")
        except Exception as e:
            # 缓存操作失败，记录日志但不影响结果返回
            logger.warning(f"缓存操作失败: {str(e)}")
        
        return result
    except HTTPException:
        # 重新抛出HTTPException
        raise
    except Exception as e:
        # 记录详细错误信息
        logger.error(f"user_data路由错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f'服务器内部错误: {str(e)}')