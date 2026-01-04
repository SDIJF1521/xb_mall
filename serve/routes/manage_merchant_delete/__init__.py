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
    """
    管理员删除商户接口
    流程：管理员Token验证 -> 检查商户是否存在 -> 删除商户记录
    注意：删除操作不可逆，会删除商户的所有数据
    """
    verify = ManagementTokenVerify(token=data.token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()

    async def execute():
        sql_data= await execute_db_query(db,'select * from mall_info where user = %s',(data.name))
        if sql_data:
            # 删除商户记录（级联删除相关数据）
            await execute_db_query(db,"DELETE FROM mall_info WHERE user = %s",(data.name))
            return {"code":200,"msg":"删除成功","success":True}
        else:
            return {"code":404,"msg":"用户不存在","success":False}
    try:    
        sql_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
        Verify_data = await verify.run(sql_data)
        if Verify_data['current']:
            return await execute()
        else:
            return {'current':False,'msg':'验证失败','code':401}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
