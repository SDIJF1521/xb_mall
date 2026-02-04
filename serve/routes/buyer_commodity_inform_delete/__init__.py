from typing import Annotated


from aiomysql import Connection
from bson import ObjectId
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerReadCommodityInfoDelete
from data.sql_client_pool import get_db_pool,db_pool
from data.redis_client import get_redis,RedisClient
from data.mongodb_client import get_mongodb_client,MongoDBClient

router = APIRouter()
@router.post('/buyer_r_commodity_inform_delete')
async def buyer_r_commodity_inform_delete(data:Annotated[BuyerReadCommodityInfoDelete,Form(...)],
                                          db:Connection = Depends(get_db_pool),
                                          redis:RedisClient = Depends(get_redis),
                                          mongodb:MongoDBClient = Depends(get_mongodb_client)):
    
    """删除商品通知"""
    verify_duter_token = VerifyDuterToken(data.token, redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool
    
    if token_data is None:
        return {'code': 403, 'msg': 'token验证失败', 'current': False}
    
    async def execute(mall_id_list):
        """执行删除操作"""
        try:
            object_id = None
            if data.info_id:
                try:
                    object_id = ObjectId(data.info_id)
                except Exception:
                    return {
                        'code': 400,
                        'msg': '无效的 info_id 格式',
                        'current': False
                    }
            
            filter_dict = {
                'mall_id': {'$in': mall_id_list},
            }
            if object_id:
                filter_dict["_id"] = {"$ne": object_id}

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
                }
                if object_id:
                    filter_dict["_id"] =  object_id
            
            updated_count = await mongodb.count_documents(
                'commodity_msg',
                filter_dict
            )
            
            cache = CacheService(redis)
            await cache.delete_pattern('commodity:inform:*')
            print
            if updated_count > 0:
                updated_count = await mongodb.delete_many(
                'commodity_msg',
                filter_dict
            )
                return {
                    'code': 200,
                    'msg': '删除成功',
                    'current': True,
                    'updated_count': updated_count
                }
            else:
                return {
                    'code': 400,
                    'msg': '通知不存在',
                    'current': False,
                    'updated_count': 0
                }
        except Exception as e:
            return {
                'code': 500,
                'msg': f'标记已读失败: {str(e)}',
                'current': False
            }
    
    if token_data.get('station') == '1':
    
        sql_data = await sql.execute_query(
            'select user from seller_sing where user = %s',
            (token_data.get('user'),)
        )
        verify_data = await verify_duter_token.verify_token(sql_data)
        print(verify_data)
        if verify_data[0]:
            if data.mall_id not in token_data.get('state_id_list'):
                return {'code': 403, 'msg': '您没有权限操作该店铺的通知', 'current': False}
            mall_id_list = token_data.get('state_id_list', [])
            if not mall_id_list:
                return {'code': 400, 'msg': '用户没有关联的店铺', 'current': False}
            print(data.info_id)
            return await execute(mall_id_list)
        else:
            return {'code': 403, 'msg': '验证失败', 'current': False}
    else:
        role_authority_service = RoleAuthorityService(
            role=token_data.get('role'),
            db=db,
            redis=redis,
            name=token_data.get('user'),
            mall_id=token_data.get('mall_id')
        )
        role_authority = await role_authority_service.get_authority(
            token_data.get('mall_id')
        )
        execute_code = await role_authority_service.authority_resolver(
            int(role_authority[0][0])
        )
        
        sql_data = await sql.execute_query(
            'select user from store_user where user = %s and store_id = %s',
            (token_data.get('user'), token_data.get('mall_id'))
        )
        verify_data = await verify_duter_token.verify_token(sql_data)
        
        if execute_code[2] and verify_data[0]:
            if data.mall_id != token_data.get('mall_id'):
                return {'code': 403, 'msg': '您没有权限操作该店铺的通知', 'current': False}
            mall_id = token_data.get('mall_id')
            if not mall_id:
                return {'code': 400, 'msg': '用户没有关联的店铺', 'current': False}
            return await execute([mall_id])
        else:
            return {'code': 403, 'msg': '您没有权限执行此操作', 'current': False}