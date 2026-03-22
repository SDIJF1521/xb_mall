from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Header

from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.sql_client_pool import get_db_pool,db_pool
from data.redis_client import RedisClient,get_redis

router = APIRouter()
@router.post('/buter_exit',summary="买家退出登录")
async def buter_exit(access_token:str=Header(min_length=6),db:Connection=Depends(get_db_pool),redis:RedisClient=Depends(get_redis)):
    """退出登录"""
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool

    async def execute(user_name:str,station:str,store_id:int = None):
        try:
            cache = CacheService(redis)
            if store_id is None and station == '1':
                await cache.delete(f"buyer_{user_name}")
                return {'code':200,'msg':'退出成功','current':True}
            elif store_id is not None and station == '2':
                await cache.delete(f"buyer_{store_id}_{user_name}")
                return {'code':200,'msg':'退出成功','current':True}
            else:
                return {'code':400,'msg':'退出失败','current':False}
        except Exception as e:
            return {'code':500,'msg':'退出失败,内部错误','current':False}


    if token_data.get('station') == '1':
        sql_data = await sql.execute_query('select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data[0]:
            return await execute(token_data.get('user'),token_data.get('station'))
        else:
            return {'code':400,'msg':'token验证失败','current':False}
    else:
        sql_data = await sql.execute_query('select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data[0]:
            return await execute(token_data.get('user'),token_data.get('station'),token_data.get('mall_id'))
        else:
            return {'code':400,'msg':'token验证失败','current':False}