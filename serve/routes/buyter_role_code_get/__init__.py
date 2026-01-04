from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter, Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.data_mods import BuyerRoleCodeGet
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.post('/buyer_role_code_get')
async def buyer_role_code_get(data:Annotated[BuyerRoleCodeGet,Form()],
                              db:Connection =Depends(get_db),
                              redis:RedisClient=Depends(get_redis)):
    """
    获取权限码列表接口
    流程：Token验证 -> 权限检查 -> 查询所有权限码（用于角色权限配置）
    权限：主商户直接通过，店铺用户需要查询权限[2]
    返回：权限码字典列表 {权限码值: 权限名称}
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    
    async def execute():
        # 查询所有权限码（用于角色权限配置界面）
        role_code_data = await execute_db_query(db,"select * from role_code")
        if role_code_data:
            # 构建权限码字典：{权限码值: 权限名称}
            out_data = [{i[0]:i[1]} for i in role_code_data]
            return {"code":200,"msg":"success","data":out_data,'current':True}
        else:
             return {"code":400,"msg":"no role code","data":None,'current':False}
        
    try:
        if token_data.get('station') == '1':
                sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
                verify_data = await verify_duter_token.verify_token(sql_data)
                if verify_data:
                    return await execute()
        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            # 需要查询权限[2]
            if execute_code[2] and verify_data:
                 return await execute()
            else:
               return {"code":400,"msg":"权限不足","data":None,'current':False}
    except HTTPException as e:
        return {"code":e.status_code,"msg":e.detail,"data":None,'current':False}