import base64

import aiomysql
from fastapi import APIRouter, Form, HTTPException, Depends

from data.sql_client import get_db, execute_db_query
from data.redis_client import get_redis,RedisClient
from services.user_info import UserInfo
from services.cache_service import CacheService
router = APIRouter()

@router.post("/userinfo")
async def userinfo(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)) -> dict:
    """获取用户详细信息"""
    try:
        user_info = UserInfo(token)
        info = await user_info.token_analysis()
        
        if not info.get('current'):
            return {'msg': info.get('msg', 'token无效'), 'current': False}
        
        cache = CacheService(redis)
        cache_key = cache._make_key('user:info', info['user'])
        
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        database_data = await execute_db_query(db,'select user FROM user WhERE user = %s', info['user'])
        
        if not database_data or len(database_data) == 0:
            bloom_item_id = f"user:{info['user']}"
            exists = await cache.bloom_filter.exists(bloom_item_id)
            if not exists:
                await cache.bloom_filter.add(bloom_item_id)
                return {'msg':'用户不存在','current':False}
        
        try:
            sql = await user_info.read(database_data)
        except ValueError as e:
            # 用户不存在的情况
            await cache.bloom_filter.add(f"user:{info['user']}")
            return {'msg': str(e), 'current': False}
        
        if not sql.get('current'):
            # 权限问题或其他错误，返回错误信息
            return {'msg': sql.get('msg', '查询失败'), 'current': False}
        
        # 查询详细信息
        data = await execute_db_query(db, sql['query'], sql['params'])
        if not data or len(data) == 0:
            return {'msg':'用户详细信息不存在','current':False}
        
        out_data = list(data[0])
        try:
            if not out_data[4] is None:
                with open(out_data[4],'rb') as f:
                    out_data[4] = base64.b64encode(f.read()).decode('utf-8')
        except:
            out_data[4] = ''
        
        result = {'data':out_data,'current':True}
        # 缓存结果
        await cache.set(cache_key, result, expire=300)
        # 添加到布隆过滤器（用户存在）
        await cache.bloom_filter.add(f"user:{info['user']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')