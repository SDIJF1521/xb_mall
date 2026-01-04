from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Header,Query,Depends,HTTPException

from services.buyer_role_authority import RoleAuthorityService
from services.verify_duter_token import VerifyDuterToken

from data.data_mods import RoleRatio
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()

@router.get("/buyer_role_ratio")
async def role_ratio(data:Annotated[RoleRatio,Query()],
                     access_token:Annotated[str,Header(...)],
                     db:Connection = Depends(get_db),
                     redis:RedisClient = Depends(get_redis)):
    """
    获取角色用户统计比例接口
    流程：Token验证 -> 权限检查 -> 查询角色列表 -> 统计各角色用户数量
    权限：主商户直接通过，店铺用户需要查询权限[2]
    """
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()
    
    async def execute():
        # 查询店铺的角色列表（包含全局角色和店铺角色）
        sql = '''select id,name from store_role where mall_id = %s or mall_id is Null'''
        role_data = await execute_db_query(db,sql,(data.stroe_id))
        role_dict = {role[0]:role[1] for role in role_data}
        
        # 统计各角色的用户数量
        n_sql = '''SELECT authority, COUNT(*) FROM store_user GROUP BY authority; '''
        authority_data = await execute_db_query(db,n_sql)
        authority_dict = {authority[0]:authority[1] for authority in authority_data}
        
        # 构建角色统计数据（角色ID、角色名称、用户数量）
        role_ratio_data = []
        for role_id,role_name in role_dict.items():
            role_ratio_data.append({
                'role_id':role_id,
                'role_name':role_name,
                'user_count':authority_dict.get(role_id,0)
            })
        return {'code':200,'msg':'成功','data':role_ratio_data,'current':True}

    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            return {'code':403,'msg':'验证失败','data':None,'current':False}
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
           return {'code':403,'msg':'权限不足','data':None,'current':False}
