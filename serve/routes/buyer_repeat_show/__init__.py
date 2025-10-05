from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken

from data.data_mods import AddMallData
from data.redis_client import RedisClient
from data.sql_client import get_db,execute_db_query

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()
# 买家端重复店铺检测路由
@router.post('/buyer_repeat_show')
async def check_mall_name(data:Annotated[AddMallData,Form()],db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    verify = VerifyDuterToken(token=data.token,redis_client=redis)
    verify_data = await verify.token_data()
    sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(verify_data.get('user')))
    verify_val = await verify.verify_token(sql_data)
    if verify_val[0]:
        sql_mall_data = await execute_db_query(db,
                                               "select user from store where user = %s and mall_name = %s and mall_phone = %s and mall_site = %s and mall_describe = %s",
                                               (data.user,data.mall_name,data.mall_phone,data.mall_site,data.info))
        if sql_mall_data:
            return {"code": 200,"msg":"该店铺已存在",'current':True}
        else:
            return {"code": 200,"msg":"该店铺不存在",'current':False}
    else:
        return {"code": 400,"msg":"token过期",'current':False}
    