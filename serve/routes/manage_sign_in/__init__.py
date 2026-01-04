from typing import Annotated

import aiomysql
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter,Depends,HTTPException

from data.data_mods import ManageSignIn
from data.sql_client import get_db, execute_db_query

from services.manage_login import ManageLogin

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/manage_sign_in')
async def manage_sign_in(data:OAuth2PasswordRequestForm=Depends(),db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    """
    管理员登录接口（OAuth2标准格式）
    流程：查询管理员账号 -> 验证密码 -> 生成JWT Token -> 存储过期时间到Redis
    用途：管理员登录获取Token
    """
    try:
        database_data =  await execute_db_query(db,'select user,password FROM manage_user WhERE user = %s',data.username)
        manage_login = ManageLogin(user=data.username,password=data.password,redis_client=redis_client)
        # 验证密码并生成Token
        return await manage_login.check_password(database_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")