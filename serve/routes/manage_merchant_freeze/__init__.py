from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.management_token_verify import ManagementTokenVerify

from data.data_mods import FreezeMerchant
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()

@router.post("/manage_merchant_freeze")
async def freeze_merchant(data:Annotated[FreezeMerchant,Form()],
                          db:Connection = Depends(get_db),
                          redis:RedisClient = Depends(get_redis)):
    
    verify = ManagementTokenVerify(token=data.token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()

    async def execute():
        sql_data = await execute_db_query(db,
                                          "SELECT * FROM mall_info WHERE user = %s AND mall_state = 1",
                                          (data.name,))
        if sql_data:
            await execute_db_query(db,
                                   "UPDATE mall_info SET mall_state = %s WHERE user = %s",
                                   (2,data.name))

            return {"code":200,"msg":"冻结成功","success":True}
        else:
            return {"code":404,"msg":"用户不存在或已被冻结","success":False}
        
    try:
        if admin_tokrn_content['current']:
            return await execute()
        else:
            return {"code":403,"msg":"token错误","success":False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))