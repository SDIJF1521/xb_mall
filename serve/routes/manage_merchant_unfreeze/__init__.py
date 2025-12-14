from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.management_token_verify import ManagementTokenVerify

from data.data_mods import FreezeMerchant
from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db,execute_db_query

router = APIRouter()

@router.post("/manage_merchant_unfreeze")

async def thaw_merchant(
    data: Annotated[FreezeMerchant, Form()],
    db: Annotated[Connection, Depends(get_db)],
    redis: Annotated[RedisClient, Depends(get_redis)]
):
    """解冻商家"""
    verify = ManagementTokenVerify(token=data.token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()

    async def execute():
        sql_data = await execute_db_query(db,
                                          "SELECT * FROM mall_info WHERE user = %s AND mall_state = 2",
                                          (data.name,))
        if sql_data:
            await execute_db_query(db,
                                   "UPDATE mall_info SET mall_state = %s WHERE user = %s",
                                   (1,data.name))

            return {"code":200,"msg":"解冻成功","success":True}
        else:
            return {"code":404,"msg":"用户不存在或未被冻结","success":False}
        
    try:
        if admin_tokrn_content['current']:
            return await execute()
        else:
            return {"code":403,"msg":"token错误","success":False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))