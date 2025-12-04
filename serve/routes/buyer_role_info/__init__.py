from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Query,Header

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.data_mods import BuyerRoleInfo
from data.sql_client import execute_db_query,get_db
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.get("/buyer_role_info")
async def buyer_role_info(data:Annotated[BuyerRoleInfo,Query()],
                          access_token:Annotated[str,Header(...)],
                          db:Connection = Depends(get_db),
                          redis:RedisClient = Depends(get_redis)):
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()

    # 执行函数
    async def execute():
        sql = "select * from store_role where id = %s and mall_id = %s"
        role_data = await execute_db_query(db,sql,(data.role_id,data.stroe_id))
        if role_data:
            role_authority_service = RoleAuthorityService(data.role_id,db)
            role_authority = await role_authority_service.get_authority(data.stroe_id)
            role_execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql = "select code from role_code"
            role_code = await execute_db_query(db,sql)
            if role_authority:
                out = [role_code[i][0] for i in range(len(role_execute_code)) if role_execute_code[i]]
                return {'code':200,'msg':'获取角色信息成功','current':True,"data":{"name":role_data[0][3],"role":role_data[0][1],"authority":out}}
            else:
                return {'code':400,'msg':'角色不存在','current':False}
        else:
            return {'code':400,'msg':'角色不存在','current':False}

    # 验证token与权限
    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            return {'code':400,'msg':'token验证失败','current':False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code[2] and verify_data:
            return await execute()
        else:
            return {'code':400,'msg':'权限不足','current':False}