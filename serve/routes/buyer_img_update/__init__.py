from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,UploadFile,File

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient


def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()
@router.patch('/buyer_update_img')
async def buyer_update_img(token:str = Form(...),id:str = Form(...),img:UploadFile=File(...),db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
     # 验证 token
    verify_duter_token = VerifyDuterToken(token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        with open(f"./mall_img/{id}.png", "wb") as f:
            f.write(await img.read())
        return {"code":200,"msg":"success","data":None,'current':True}

    async def execute():
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            # 保存图片到本地
            return await execute()
        else:
            return {"code":400,"msg":"token验证失败","data":None,'current':False}
            

    try:
        if token_data.get('station') == '1':
            return await execute()

        else:
            if token_data.get('role') == 1:
                return await execute()
            else:
                if token_data.get('user') == id:
                    return await execute()
                else:
                    return {"code":400,"msg":"权限不足","data":None,'current':False}
    except Exception as e:
        return {"code":400,"msg":str(e),"data":None,'current':False}