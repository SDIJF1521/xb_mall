from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient
from data.data_mods import AddMallData

router = APIRouter()

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

# 新增店铺i路由
@router.post("/add_mall")
async def add_mall(data:Annotated[AddMallData,Form()],db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    # 验证token
    verify_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_token.token_data()
    pass