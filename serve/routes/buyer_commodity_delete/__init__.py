import os
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerDeleteCommodity
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.delete("/buyer_commodity_delete")
async def buyer_commodity_delete(data:Annotated[BuyerDeleteCommodity,Form()],
                                db:Connection=Depends(get_db),
                                redis:RedisClient=Depends(get_redis),
                                mongodb:MongoDBClient=Depends(get_mongodb_client)):
    """
    买家删除商品接口
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        cache = CacheService(redis)
        await execute_db_query(db,
                              'delete from shopping where shopping_id = %s and mall_id =  %s ',
                              (data.shopping_id,data.stroe_id))
        await execute_db_query(db,
                               'delete from specification where mall_id = %s and shopping_id = %s',
                               (data.stroe_id,data.shopping_id))
        await mongodb.delete_many(
            'shopping',
            {'mall_id':data.stroe_id,'shopping_id':data.shopping_id}
        )
        await mongodb.delete_many(
            'commodity_msg',
            {'mall_id':data.stroe_id,'shopping_id':data.shopping_id}
        )
        img_dir = f'./shopping_img/{data.stroe_id}_{data.shopping_id}'
        try:
            if os.path.exists(img_dir):
                import shutil
                for root, dirs, files in os.walk(img_dir):
                    for file in files:
                        img_path = os.path.join(root, file)
                        img_cache_key = cache._make_key('img_base64', img_path)
                        await cache.delete(img_cache_key)
                shutil.rmtree(img_dir)
        except:
            pass
        await cache.delete_pattern(f'commodity:list:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:search:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:inform:*')
        await cache.delete_pattern(f'admin:commodity:detail:{data.stroe_id}:{data.shopping_id}')
        await cache.delete_pattern(f'admin:commodity:apply:*')
        await cache.delete_pattern(f'img_base64:*')
        await cache.delete_pattern(f'commodity:repertory:list:{data.stroe_id}')
        await cache.delete_pattern(f'commodity:repertory:search:{data.stroe_id}:*')
        return {'code':200,'msg':'删除成功','current':True}

    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            return {'code':400,'msg':'验证失败','current':False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code[3] and verify_data:
            return await execute()
        else:
            return {'code':400,'msg':'验证失败','current':False}
            