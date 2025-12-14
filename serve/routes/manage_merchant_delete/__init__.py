from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.management_token_verify import ManagementTokenVerify

from data.data_mods import DeleteMerchant
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()

@router.delete("/manage_merchant_delete")
async def manage_merchant_delete(data:Annotated[DeleteMerchant,Form()],
                                 db:Connection = Depends(get_db),
                                 redis:RedisClient=Depends(get_redis)):
    verify = ManagementTokenVerify(token=data.token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()

    async def execute():
        sql_data= await execute_db_query(db,'select * from mall_info where user = %s',(data.name))
        if sql_data:
            await execute_db_query(db,"DELETE FROM mall_info WHERE user = %s",(data.name))
            return {"code":200,"msg":"删除成功","success":True}
        else:
            return {"code":404,"msg":"用户不存在","success":False}
    try:    
        if admin_tokrn_content['current']:
            return await execute()
        else:
            return {"code":403,"msg":"token错误","success":False}
    except HTTPException as e:
        return {"code":500,"msg":str(e),"success":False}
