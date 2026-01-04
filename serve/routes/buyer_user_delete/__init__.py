import os
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Form

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.data_mods import DeleteMallUser
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()

@router.delete('/buyer_user_delete')
async def buyer_user_delete(data:Annotated[DeleteMallUser,Form()],
                            db:Connection=Depends(get_db),
                            redis:RedisClient=Depends(get_redis)):
    """
    删除店铺用户接口（支持批量删除）
    流程：Token验证 -> 权限检查 -> 防止删除自己 -> 删除用户记录 -> 删除用户头像文件
    权限：主商户直接通过，店铺用户需要删除权限[3]和分配权限[4]
    安全：不能删除自己
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()    

    async def execute():
        # 批量删除用户（支持删除多个用户）
        for i in data.user_name:
            # 删除用户记录
            await execute_db_query(db,'delete from store_user where store_id = %s and user=%s',(data.strore_id,i))
            
            # 删除用户头像文件（如果存在）
            img = await execute_db_query(db,'select img from store_user where store_id = %s and user=%s',(data.strore_id,i))
            if img:
                os.remove(img[0][0])
        return {'code':200,'msg':'删除成功','current':True}
        
        
    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {'code':400,'msg':'用户不存在','current':False}
        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            
            # 需要删除权限[3]和分配权限[4]
            if execute_code[3] and execute_code[4]:
                sql_data = await execute_db_query(db,'select user from store_user where store_id = %s and user = %s',(data.strore_id,token_data.get('user')))
                verify_data = await verify_duter_token.verify_token(sql_data)
                if verify_data:
                    # 安全保护：不能删除自己
                    if token_data.get('user') in data.user_name:
                        return {'code':400,'msg':'不能删除自己','current':False}
                    return await execute()
                else:
                    return {'code':400,'msg':'token验证失败','current':False}
            else:
                return {'code':400,'msg':'权限不足','current':False}
    except HTTPException as e:
        return {'code':400,'msg':e.detail,'current':False}
    except:
        return {'code':500,'msg':'无效参数','current':False}
            
