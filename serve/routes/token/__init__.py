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
    用户登录获取Token接口（OAuth2标准格式）
    流程：查询用户信息 -> 验证密码 -> 生成JWT Token -> 存储过期时间到Redis
    """
    try:
        database_data = await execute_db_query(db,'select user,password FROM user WhERE user = %s',form_data.username)
        token = Token(form_data.username,form_data.password)
        return await token.make(database_data,redis_cli=redis_cli)
    except Exception as e:
          raise HTTPException(status_code=500, detail="服务器内部错误")