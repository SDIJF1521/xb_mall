from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException,Header

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client
from data.data_mods import BuyerReadCommodityInform

router = APIRouter()

@router.post("/buyer_r_commodity_inform_read")
async def buyer_r_commodity_inform_read(
    data: Annotated[BuyerReadCommodityInform, Form()],
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client)
):
    """标记商品通知为已读"""
    verify_duter_token = VerifyDuterToken(data.token, redis)
    token_data = await verify_duter_token.token_data()
    
    if token_data is None:
        return {'code': 403, 'msg': 'token验证失败', 'current': False}
    
    async def execute(mall_id_list):
        """执行标记已读操作"""
        try:
            filter_dict = {
                'mall_id': {'$in': mall_id_list},
                'read': 0
            }

            if data.mall_id is not None and data.shopping_id is not None:
                if data.mall_id not in mall_id_list:
                    return {
                        'code': 403,
                        'msg': '您没有权限操作该店铺的通知',
                        'current': False
                    }
                filter_dict = {
                    'mall_id': data.mall_id,
                    'shopping_id': data.shopping_id,
                    'read': 0
                }
            
            update_dict = {'$set': {'read': 1}}
            updated_count = await mongodb.update_many(
                'commodity_msg',
                filter_dict,
                update_dict
            )
            
            cache = CacheService(redis)
            await cache.delete_pattern('commodity:inform:*')
            
            if updated_count > 0:
                return {
                    'code': 200,
                    'msg': '标记已读成功',
                    'current': True,
                    'updated_count': updated_count
                }
            else:
                return {
                    'code': 200,
                    'msg': '没有需要标记的通知',
                    'current': True,
                    'updated_count': 0
                }
        except Exception as e:
            return {
                'code': 500,
                'msg': f'标记已读失败: {str(e)}',
                'current': False
            }
    
    if token_data.get('station') == '1':
    
        sql_data = await execute_db_query(
            db,
            'select user from seller_sing where user = %s',
            (token_data.get('user'),)
        )
        verify_data = await verify_duter_token.verify_token(sql_data)
        
        if verify_data[0]:
            mall_id_list = token_data.get('state_id_list', [])
            if not mall_id_list:
                return {'code': 400, 'msg': '用户没有关联的店铺', 'current': False}
            return await execute(mall_id_list)
        else:
            return {'code': 403, 'msg': '验证失败', 'current': False}
    else:
        role_authority_service = RoleAuthorityService(
            token_data.get('role'),
            db
        )
        role_authority = await role_authority_service.get_authority(
            token_data.get('mall_id')
        )
        execute_code = await role_authority_service.authority_resolver(
            int(role_authority[0][0])
        )
        
        sql_data = await execute_db_query(
            db,
            'select user from store_user where user = %s and store_id = %s',
            (token_data.get('user'), token_data.get('mall_id'))
        )
        verify_data = await verify_duter_token.verify_token(sql_data)
        
        if execute_code[2] and verify_data:
            mall_id = token_data.get('mall_id')
            if not mall_id:
                return {'code': 400, 'msg': '用户没有关联的店铺', 'current': False}
            return await execute([mall_id])
        else:
            return {'code': 403, 'msg': '您没有权限执行此操作', 'current': False}
