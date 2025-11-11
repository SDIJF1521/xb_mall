from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken

from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db,execute_db_query
from data.data_mods import AddMallUser

router = APIRouter()
@router.post('/buyer_user_add')
async def buyer_user_add(data:Annotated[AddMallUser,Form()],db:Connection = Depends(get_db),redis:RedisClient = Depends(get_redis)):

    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    # 操作执行函数
    async def execute():
        sql_user = await execute_db_query(db,
                                          "select user from store_user where store_id=%s and user=%s",
                                          (data.strore_id,data.user_name))
        if sql_user:
            return {"code":400,"msg":"用户已存在","data":None,'current':False}
        sql_role = await execute_db_query(db,
                                          "select id from store_role where mall_id is null or mall_id=%s",
                                          (data.strore_id))
        role_list = [item[0] for item in sql_role]
        # 检查权限是否存在
        print(sql_user)
        if data.authority not in role_list:
            return {"code":400,"msg":"用户权限不存在","data":None,'current':False}
        if not sql_user:
            await execute_db_query(db,
                "INSERT INTO store_user (store_id,user,password,authority,email) VALUES (%s,%s,%s,%s,%s)",
                (data.strore_id,data.user_name,data.user_password,data.authority,data.email)
            )
            return {"code":200,"msg":"操作成功","data":None,'current':True}
        else:
            return {"code":400,"msg":"用户已存在","data":None,'current':False}
    
    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            raise HTTPException(status_code=400, detail="验证失败")
    else:
        if token_data.get('role') == '1':
            return await execute()
        else:
            raise HTTPException(status_code=400, detail="权限不足")