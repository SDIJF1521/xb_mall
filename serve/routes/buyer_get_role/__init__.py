from typing import Annotated

from fastapi import APIRouter,HTTPException,Depends,Form

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.data_mods import BuyerGetRole
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()

@router.post('/buyer_get_role')
async def change_user_role(
    data:Annotated[BuyerGetRole,Form()],
    db: get_db = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    """
    获取角色列表接口（支持搜索）
    流程：Token验证 -> 权限检查 -> 查询角色列表（支持按角色标识或名称搜索）
    权限：主商户直接通过，店铺用户需要查询权限[2]
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute(id,select_data:str = None):
        # 根据搜索条件查询角色（支持店铺级和全局角色）
        if select_data is not None:
            query = """
            SELECT * FROM store_role WHERE (mall_id = %s OR mall_id is Null) AND (role = %s OR name = %s)
            """
            result = await execute_db_query(db, query, (id, select_data,select_data))
        else:
            query = """
            SELECT * FROM store_role WHERE mall_id = %s OR mall_id is Null
            """
            result = await execute_db_query(db, query, (id))
        
        data = {}
        if result:
            # 构建角色数据：{角色ID: [角色标识, 角色名称, 店铺ID]}
            data = [{i[0]:[i[1],i[3],i[2]]} for i in result]
            return {'code':200,'msg':'操作成功','data':data,'current':True}
        else:
            return {'code':400,'msg':'操作失败','data':data,'current':False}
    
    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute(data.stroe_id,data.select_data)
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        # 需要查询权限[2]
        if execute_code[2]and verify_data:
            return await execute(data.stroe_id,data.select_data)
        else:
            return {'code':400,'msg':'权限不足','data':data,'current':False}
        
