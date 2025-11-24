from typing import Annotated
from base64 import b64encode

from fastapi import APIRouter,Depends,Form,HTTPException
from aiomysql import Connection


from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import GetMallUserList


router = APIRouter()

@router.post('/buyer_mall_user_list')

async def buyer_mall_user_list(data:Annotated[GetMallUserList,Form()],db:Connection = Depends(get_db),redis:RedisClient = Depends(get_redis)):
    async def execute(id):
        
            sql_user_list = await execute_db_query(db,'select * from store_user where store_id = %s',(id))
            if sql_user_list:
                data = [{'user':i[1],'password':i[2],'authority':i[3],'email':i[4],'img':i[5] if i[5] is not None else './buyer_use_img/通用/通用.png'}for i in sql_user_list]
                print(data)
                for i in data:
                    with open(i['img'], 'rb') as image_file:
                        encoded_string = b64encode(image_file.read()).decode('utf-8')
                        i['img'] = encoded_string
                return {'code':200,'msg':'获取成功','data':data,'current':True}
            else:
                return {'code':400,'msg':'店铺不存在用户','current':False}
        

    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute(data.id)
            else:
                return {'code':400,'msg':'token验证失败','current':False}

        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if execute_code[1] and execute_code[4] and verify_data:
                return await execute(data.id)
            else:
                return {'code':400,'msg':'权限不足'}
    except HTTPException as e:
        return {'code':e.status_code,'msg':e.detail,'current':False}

        
