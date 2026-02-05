from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerCommodityClassifyEdit
from data.sql_client_pool import get_db_pool,db_pool
from data.redis_client import get_redis,RedisClient

router = APIRouter()
@router.patch("/buyer_classify_edit",summary="买家编辑商品分类")
async def buyer_classify_edit(data:Annotated[BuyerCommodityClassifyEdit,Form(...)],
                              db:Connection = Depends(get_db_pool),
                              redis:RedisClient = Depends(get_redis)):
    """
    编辑商品分类
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool

    async def execute():
        cache = CacheService(redis)
        sql_classify = await db_pool.execute_query('select * from classify where store_id = %s and id = %s',
                                                    (data.stroe_id,data.classify_id))
        print(sql_classify)
        if not sql_classify:
            return {'code':400,'msg':'商品分类不存在','current':False}
        
        await sql.execute_query('update classify set name = %s where store_id = %s and id = %s',
                                (data.name,data.stroe_id,data.classify_id))
        
        await cache.delete_pattern(f'commodity:list:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:search:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:inform:*')
        await cache.delete_pattern(f'admin:commodity:detail:{data.stroe_id}:*')
        await cache.delete_pattern(f'admin:commodity:apply:*')
        await cache.delete_pattern(f'classify:{data.stroe_id}')
        await cache.delete_pattern(f'commodity:repertory:all:{data.stroe_id}')
        return {'code':200,'msg':'修改成功','current':True}
        

    if token_data.get('station') == '1':
        sql_data = await sql.execute_query('select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data[0]:
            if data.stroe_id not in token_data.get('state_id_list'):
                return {"code":400,"msg":"权限不足","data":None,'current':False}
            return await execute()
        else:
            return {"code":400,"msg":"验证失败","data":None,'current':False}
    else:
        role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                      db=db,
                                                      redis=redis,
                                                      name=token_data.get('user'),
                                                      mall_id=token_data.get('mall_id'))
        
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await sql.execute_query('select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code[1] and execute_code[4] and verify_data[0]:
            if data.stroe_id != token_data.get('mall_id'):
                return {"code":400,"msg":"权限不足","data":None,'current':False}
            return await execute()
        else:
            return {"code":400,"msg":"权限不足","data":None,'current':False}