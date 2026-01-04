from typing import Annotated
from base64 import b64encode

from aiomysql import Connection
from fastapi import APIRouter,Form,Depends,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.data_mods import SelectMallUser
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()

@router.post('/buyer_user_select')
async def buyer_user_select(data:Annotated[SelectMallUser,Form()],db:Connection = Depends(get_db),redis:RedisClient = Depends(get_redis)):
    """
    查询指定店铺用户信息接口
    流程：Token验证 -> 权限检查 -> 查询用户信息 -> 图片转Base64编码
    权限：主商户直接通过，店铺用户需要查询权限[2]和分配权限[4]
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute(id,user):
        # 查询指定店铺的指定用户信息
        sql_user = await execute_db_query(db,'select * from store_user where store_id = %s and user = %s',
                                            (id,user))
        if sql_user:
            # 构建用户数据，处理默认头像路径
            data = [{'user':i[1],'password':i[2],'authority':i[3],'email':i[4],'img':i[5] if len(i) == 6 else './buyer_use_img/通用/通用.png'}for i in sql_user]
            # 将用户头像转为Base64编码
            for i in data:
                with open(i['img'], 'rb') as image_file:
                    encoded_string = b64encode(image_file.read()).decode('utf-8')
                    i['img'] = encoded_string
            return {'code':200,'msg':'获取成功','data':data,'current':True}
        else:            
            return {'code':400,'msg':'用户不存在','current':False}
        

    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute(data.strore_id,data.user_name)
            else:
                return {'code':400,'msg':'token验证失败','current':False}
        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            # 需要查询权限[2]和分配权限[4]
            if execute_code[2] and execute_code[4] and verify_data:
                return await execute(data.strore_id,data.user_name)
            else:
                return {'code':400,'msg':'权限不足'}
    except HTTPException as e:
        return {'code':e.status_code,'msg':e.detail,'current':False}