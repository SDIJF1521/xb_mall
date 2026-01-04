from typing import Annotated

import aiomysql
from fastapi import APIRouter, Form,Depends,HTTPException, status

from data.sql_client import get_db,execute_db_query
from data.data_mods import GetApplySellerUser
from services.management_token_verify import ManagementTokenVerify

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/get_apply_seller_user')
async def get_apply_seller_user(data:Annotated[GetApplySellerUser,Form()],db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    """
    管理员按名称查询商户申请接口
    流程：管理员Token验证 -> 按名称查询申请记录
    权限：仅管理员可访问
    """
    try:
        verify = ManagementTokenVerify(token=data.token,redis_client=redis_client)
        sql_data = await execute_db_query(db,'select user from manage_user')
        verify_data = await verify.run(sql_data)
        if verify_data['current']:
            # 按名称查询商户申请
            result = await execute_db_query(db,'select * from shop_apply where name=%s',data.name)
            if result:
                return {'current':True,'apply_list':[list(i) for i in result]}
            else:
                return {'current':False,'msg':'未查询到该用户的申请'}
        else:
            return {'current':False,'msg':'token验证失败'}
    except Exception as e:
       HTTPException(status_code=500, detail=str(e))
