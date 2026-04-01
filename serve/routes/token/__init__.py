import aiomysql
from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient

from services.log_in_token import Token

router = APIRouter()


def get_redis():
    from main import redis_client
    return redis_client

@router.post('/token')
async def user_token(form_data: OAuth2PasswordRequestForm = Depends(), db:aiomysql.Connection = Depends(get_db),redis_cli:RedisClient = Depends(get_redis)) -> dict:
    """
    用户登录获取Token
    """
    try:
        status_rows = await execute_db_query(
            db,
            "SELECT status FROM `user` WHERE user = %s",
            (form_data.username,),
        )
        if status_rows and len(status_rows[0]) > 0 and status_rows[0][0] == 1:
            return {'msg': '该账号已被冻结，请联系管理员', 'token': None}

        database_data = await execute_db_query(db,'select user,password FROM user WhERE user = %s',form_data.username)
        token = Token(form_data.username,form_data.password)
        return await token.make(database_data,redis_cli=redis_cli)
    except Exception as e:
          raise HTTPException(status_code=500, detail="服务器内部错误")