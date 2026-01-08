from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService
from services.buyer_role_authority import RoleAuthorityService

from data.data_mods import BuyerDelistingCommodity
from data.sql_client_pool import DatabasePool, get_db_pool
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.post('/buyer_commodity_delisting')
async def buyer_commodity_delisting(data:Annotated[BuyerDelistingCommodity,Form()],
                                    db:Connection=Depends(get_db_pool),
                                    redis:RedisClient=Depends(get_redis),
                                    mongodb:MongoDBClient=Depends(get_mongodb_client)):
    """
    买家下架商品接口
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    sql = DatabasePool()

    async def execute():
        cache = CacheService(redis)
        sql_commodity = await sql.execute_query('select * from shopping where mall_id = %s and (shopping_id = %s and audit = 1)',
                                                (data.stroe_id,data.shopping_id))
        mongodb_commodity = await mongodb.find_one('shopping',{'mall_id':data.stroe_id,'shopping_id':data.shopping_id,'audit':1})
        print(sql_commodity)
        if mongodb_commodity and sql_commodity:
            await sql.execute_query('update shopping set audit = 3 where mall_id = %s and shopping_id = %s',(data.stroe_id,data.shopping_id))
            await mongodb.update_one('shopping',{'mall_id':data.stroe_id,'shopping_id':data.shopping_id},
                                    {'$set':{'audit':3}})
            # 移除redis相关缓存信息
            await cache.delete_pattern(f'commodity:list:{data.stroe_id}:*')
            await cache.delete_pattern(f'commodity:search:{data.stroe_id}:*')
            await cache.delete_pattern(f'commodity:inform:*')
            await cache.delete_pattern(f'admin:commodity:detail:{data.stroe_id}:{data.shopping_id}')
            await cache.delete_pattern(f'admin:commodity:apply:*')
            return {'code':200,'msg':'下架成功','current':True}
        else:
            return {'code':404,'msg':'商品不存在或已下架','current':False}

    try:
        if token_data.get('station') == '1':
            sql_data = await sql.execute_query('select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {'code':400,'msg':'token验证失败','current':False}
        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            if execute_code[3] and execute_code[4]:
                sql_data = await sql.execute_query('select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
                verify_data = await verify_duter_token.verify_token(sql_data)
                if verify_data:
                    return await execute()
                else:
                    return {'code':400,'msg':'token验证失败','current':False}
            else:
                return {'code':400,'msg':'您没有权限操作','current':False}
    except Exception as e:
        return {'code':500,'msg':'服务器错误','current':False}
    except HTTPException as e:
        raise e