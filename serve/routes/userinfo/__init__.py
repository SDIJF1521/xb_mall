import base64
import logging

import aiomysql
from fastapi import APIRouter, Form, HTTPException, Depends

from data.sql_client import get_db, execute_db_query
from data.redis_client import get_redis,RedisClient
from services.user_info import UserInfo
from services.cache_service import CacheService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/userinfo")
async def userinfo(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis:RedisClient=Depends(get_redis)) -> dict:
    """获取用户详细信息"""
    try:
        user_info = UserInfo(token)
        info = await user_info.token_analysis()
        
        if not info or not isinstance(info, dict):
            logger.error(f"token_analysis返回无效结果: {info}")
            return {'msg': 'token解析失败', 'current': False}
        
        if not info.get('current'):
            return {'msg': info.get('msg', 'token无效'), 'current': False}
        
        if 'user' not in info or not info['user']:
            logger.error(f"token解析结果缺少user字段: {info}")
            return {'msg': 'token中缺少用户信息', 'current': False}
        
        cache = CacheService(redis)
        cache_key = cache._make_key('user:info', info['user'])
        
        try:
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data
        except Exception as e:
            logger.warning(f"获取缓存失败，继续查询数据库 | Key: {cache_key} | 错误: {str(e)}")
        
        try:
            database_data = await execute_db_query(db,'select user FROM user WHERE user = %s', (info['user'],))
        except Exception as e:
            logger.error(f"数据库查询失败 | User: {info['user']} | 错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f'数据库查询失败: {str(e)}')
        
        if not database_data or len(database_data) == 0:
            bloom_item_id = f"user:{info['user']}"
            try:
                exists = await cache.bloom_filter.exists(bloom_item_id)
                if not exists:
                    await cache.bloom_filter.add(bloom_item_id)
            except Exception as e:
                logger.warning(f"布隆过滤器操作失败 | Item: {bloom_item_id} | 错误: {str(e)}")
            return {'msg':'用户不存在','current':False}
        
        try:
            sql = await user_info.read(database_data)
        except ValueError as e:
            try:
                await cache.bloom_filter.add(f"user:{info['user']}")
            except Exception as e2:
                logger.warning(f"布隆过滤器添加失败 | User: {info['user']} | 错误: {str(e2)}")
            return {'msg': str(e), 'current': False}
        except Exception as e:
            logger.error(f"read方法执行失败 | User: {info['user']} | 错误: {str(e)}")
            return {'msg': '用户信息读取失败', 'current': False}
        
        if not sql or not isinstance(sql, dict) or not sql.get('current'):
            return {'msg': sql.get('msg', '查询失败') if isinstance(sql, dict) else '查询失败', 'current': False}
        
        if 'query' not in sql or 'params' not in sql:
            logger.error(f"read方法返回的SQL格式不正确: {sql}")
            return {'msg': '查询配置错误', 'current': False}
        
        try:
            data = await execute_db_query(db, sql['query'], sql['params'])
        except Exception as e:
            logger.error(f"执行SQL查询失败 | Query: {sql['query']} | Params: {sql['params']} | 错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f'数据库查询失败: {str(e)}')
        
        if not data or len(data) == 0:
            return {'msg':'用户详细信息不存在','current':False}
        
        if len(data[0]) < 5:
            logger.error(f"查询结果字段数量不足 | 字段数: {len(data[0])}")
            return {'msg':'用户数据格式错误','current':False}
        
        out_data = list(data[0])
        try:
            if len(out_data) > 4 and out_data[4] is not None:
                with open(out_data[4],'rb') as f:
                    out_data[4] = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.warning(f"读取头像文件失败 | Path: {out_data[4] if len(out_data) > 4 else 'N/A'} | 错误: {str(e)}")
            if len(out_data) > 4:
                out_data[4] = ''
        
        result = {'data':out_data,'current':True}
        try:
            await cache.set(cache_key, result, expire=300)
            await cache.bloom_filter.add(f"user:{info['user']}")
        except Exception as e:
            logger.warning(f"缓存设置失败 | Key: {cache_key} | 错误: {str(e)}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"userinfo路由执行失败 | Token: {token[:20] if token else 'None'}... | 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f'服务器内部错误: {str(e)}')