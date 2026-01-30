from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerCommodityClassifyDelete
from data.sql_client_pool import get_db_pool,db_pool
from data.redis_client import RedisClient,get_redis

router = APIRouter()

# 买家删除商品分类路由
@router.delete("/buyer_classify_delete",summary="买家删除商品分类")
async def buyer_classify_delete(data:Annotated[BuyerCommodityClassifyDelete,Form(...)],
                                db:Connection = Depends(get_db_pool),
                                redis:RedisClient = Depends(get_redis)):
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool
    async def execute():
        cache = CacheService(redis)
        sql_classify_id = await sql.execute_query('select id from classify where store_id = %s and id = %s',
                                                   (data.stroe_id,data.classify_id))
        if not sql_classify_id:
            return {'code':400,'msg':'商品分类不存在','current':False}
        try:
            await sql.execute_query('delete from classify where store_id = %s and id = %s',(data.stroe_id,data.classify_id))
            await cache.delete_pattern(f'classify:{data.stroe_id}')
            return {'code':200,'msg':'删除成功','current':True}
        except Exception as e:
            return {'code':500,'msg':'删除失败，请稍后重试','current':False}

    if token_data.get('station') == '1':
        sql_data = await sql.execute_query('select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            return {'code':400,'msg':'token验证失败','current':False}
    else:
        role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                      db=db,
                                                      redis=redis,
                                                      name=token_data.get('user'),
                                                      mall_id=token_data.get('mall_id'))
        
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        if execute_code[3] and execute_code[4] and verify_data:
            return await execute()
        else:
            return {'code':400,'msg':'您没有权限执行此操作','current':False}