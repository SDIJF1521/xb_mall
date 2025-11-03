import base64
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Form,Depends

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient
from data.data_mods import GetMallInfo

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()
@router.post("/buyer_get_mall_info")
async def buyer_get_mall_info(data:Annotated[GetMallInfo,Form()],db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):
        # 验证 token
        verify_duter_token = VerifyDuterToken(data.token,redis)
        token_data = await verify_duter_token.token_data()
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                sql_mall_info = await execute_db_query(db,"select * from store where user = %s",(token_data.get("user")))
                # 返回字段处理表达式
                rtn = []
                if sql_mall_info:
                    # 假设数据库结构为：id, user, mall_name, phone, site, info, img_path, time
                    # 注意：第6个字段(i[6])应该是img_path而不是img
                    rtn = [{"id":i[0],"user":i[1],"mall_name":i[2],"phone":i[3],"site":i[4],"info":i[5],"img":i[6],"time":i[7]}for i in sql_mall_info]
                    for i in rtn:
                        with open(i['img'], 'rb') as f:
                            i['img'] = base64.b64encode(f.read()).decode('utf-8')
                return {"code":200,"msg":"success","data":rtn,'current':True}
            else:
                return {"code":400,"msg":"token verify failed","data":None,'current':False}
        else:
            return {"code":400,"msg":"token verify failed","data":None,'current':False}