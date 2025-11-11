from typing import Annotated

from fastapi import APIRouter,Depends,Form,HTTPException
from aiomysql import Connection


from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import GetMallUserList


router = APIRouter()

@router.post('/buyer_mall_user_list')

async def buyer_mall_user_list(data:Annotated[GetMallUserList,Form()],db:Connection = Depends(get_db),redis:RedisClient = Depends(get_redis)):
    async def execute(id):
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            sql_user_list = await execute_db_query(db,'select * from store_user where store_id = %s',(id))
            if sql_user_list:
                data = [{'user':i[1],'password':i[2],'authority':i[3],'email':i[4],'img':i[5]}for i in sql_user_list]
                return {'code':200,'msg':'获取成功','data':data,'current':True}
            else:
                return {'code':400,'msg':'店铺不存在用户','current':False}
        else:
            return {'code':400,'msg':'token验证失败','current':False}

    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    try:
        if token_data.get('station') == '1':
            return await execute(data.id)

        else:
            if token_data.get('role') == 1:
                return await execute(data.id)
            else:
                return {'code':400,'msg':'权限不足'}
    except HTTPException as e:
        return {'code':e.status_code,'msg':e.detail,'current':False}

        
