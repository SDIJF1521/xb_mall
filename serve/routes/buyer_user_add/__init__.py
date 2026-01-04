from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db,execute_db_query
from data.data_mods import AddMallUser

router = APIRouter()

@router.post('/buyer_user_add')
async def buyer_user_add(data:Annotated[AddMallUser,Form()],db:Connection = Depends(get_db),redis:RedisClient = Depends(get_redis)):
    """
    添加店铺用户接口
    流程：Token验证 -> 权限检查 -> 检查用户是否重复 -> 验证角色是否存在 -> 插入用户记录
    权限：主商户直接通过，店铺用户需要写入权限[1]和分配权限[4]
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        # 检查用户是否已存在
        sql_user = await execute_db_query(db,
                                          "select user from store_user where store_id=%s and user=%s",
                                          (data.strore_id,data.user_name))
        if sql_user:
            return {"code":400,"msg":"用户已存在","data":None,'current':False}
        
        # 验证角色是否存在（检查店铺角色和全局角色）
        sql_role = await execute_db_query(db,
                                          "select id from store_role where mall_id is null or mall_id=%s",
                                          (data.strore_id))
        role_list = [item[0] for item in sql_role]
        if data.authority not in role_list:
            return {"code":400,"msg":"用户权限不存在","data":None,'current':False}
        
        # 插入新用户记录
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
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        # 需要写入权限[1]和分配权限[4]
        if execute_code[1] and execute_code[4] and verify_data:
            return await execute()
        else:
            raise HTTPException(status_code=400, detail="权限不足")