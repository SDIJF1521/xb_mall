import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form

from data.sql_client import get_db,execute_db_query
from services.management_token_verify import ManagementTokenVerify

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()
@router.post('/get_apply_seller_list')
async def get_apply_seller_list(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    verify = ManagementTokenVerify(token=token,redis_client=redis_client)
    data = await execute_db_query(db,'select user from manage_user')
    Verify_data = await verify.run(data)
    if Verify_data['current']:
        sql_data = await execute_db_query(db,'select * from shop_apply where state = 0')
        if sql_data:
            user_list = [list(i) for i in sql_data]
            return {'apply_list':user_list,'current':True}
        else:
            return {'apply_list':[],'current':True}
    else:
        return {'msg':'不是管理员用户','current':False}