import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form
from data.sql_client import get_db, execute_db_query
from services.user_info import UserInfo

from services.log_in import LogIn
from data.redis_client import RedisClient
router = APIRouter()

def get_redis():
    from main import redis_client
    return redis_client

@router.post('/user_sign_in')
async def user_sgin(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis_cli:RedisClient = Depends(get_redis)) ->dict:
    """
    用户登录状态验证
    """
    try:
        user = await UserInfo(token=token).token_analysis()
        database_data = ()
        if user['current']:
            database_data = await execute_db_query(db,'select user FROM user WHERE user = %s',user['user'])
        log_in = LogIn(token=token)
        return await log_in.run(database_data,redis_cli=redis_cli)
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')
