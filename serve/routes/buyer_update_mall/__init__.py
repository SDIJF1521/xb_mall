from typing import Annotated
import os

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import UpdateMall

router = APIRouter()

@router.patch('/buyer_update_mall')
async def buyer_update_mall(data:Annotated[UpdateMall,Form()],db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    更新店铺信息接口
    流程：Token验证 -> 权限检查 -> 检查店铺是否存在 -> 更新店铺信息 -> 删除旧图片
    权限：主商户直接通过，店铺用户需要查询权限[2]、写入权限[1]和分配权限[4]
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        # 检查店铺是否存在
        sel_mall_id = await execute_db_query(db,'select * from store where mall_id=%s',(data.id))
        if sel_mall_id:
            # 更新店铺信息（名称、电话、地址、描述、状态）
            await execute_db_query(db,'update store set mall_name=%s,mall_phone=%s,mall_site=%s,mall_describe=%s,state=%s where mall_id=%s',
                                (data.mall_name,data.mall_site,data.mall_phone,data.info,data.state,data.id))
            # 删除旧店铺图片
            os.remove(f'./mall_img/{data.id}.png')
            return {"code":200,"msg":"操作成功","data":None,'current':True}
        else:
            return {"code":400,"msg":"mall_id不存在","data":None,'current':False}

    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {"code":400,"msg":"您没有权限操作","data":None,'current':False}
        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            # 需要查询权限[2]、写入权限[1]和分配权限[4]
            if execute_code[2] and execute_code[1] and execute_code[4] and verify_data:
                return await execute()
            else:
                return {"code":400,"msg":"您没有权限操作","data":None,'current':False}
    except Exception as e:
        return {"code":400,"msg":str(e),"data":None,'current':False}