from typing import Annotated
from base64 import b64encode

from aiomysql import Connection
from fastapi import APIRouter,Form,Depends,HTTPException

from services.verify_duter_token import VerifyDuterToken

from data.data_mods import SelectMallUser
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()
@router.post('/buyer_user_select')
async def buyer_user_select(data:Annotated[SelectMallUser,Form()],db:Connection = Depends(get_db),redis:RedisClient = Depends(get_redis)):
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute(id,user):
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            sql_user = await execute_db_query(db,'select * from store_user where store_id = %s and user = %s',
                                              (id,user))
            if sql_user:
                data = [{'user':i[1],'password':i[2],'authority':i[3],'email':i[4],'img':i[5] if len(i) == 6 else './buyer_use_img/通用/通用.png'}for i in sql_user]
                for i in data:
                    with open(i['img'], 'rb') as image_file:
                        encoded_string = b64encode(image_file.read()).decode('utf-8')
                        i['img'] = encoded_string
                return {'code':200,'msg':'获取成功','data':data,'current':True}
            else:            
                return {'code':400,'msg':'用户不存在','current':False}
        else:
            return {'code':400,'msg':'token验证失败','current':False}
    try:
        if token_data.get('station') == '1':
            return await execute(data.strore_id,data.user_name)
        else:
            if token_data.get('role') == 1:
                return await execute(data.strore_id,data.user_name)
            else:
                return {'code':400,'msg':'权限不足'}
    except HTTPException as e:
        return {'code':e.status_code,'msg':e.detail,'current':False}