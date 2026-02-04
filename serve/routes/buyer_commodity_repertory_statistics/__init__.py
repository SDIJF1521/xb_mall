import logging

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form, HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.sql_client_pool import get_db_pool, db_pool
from data.redis_client import get_redis, RedisClient
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/buyer_commodity_repertory_statistics")
async def buyer_commodity_repertory_statistics(
                                        token: str = Form(...),
                                        stroe_id: int = Form(...),
                                        db:Connection=Depends(get_db_pool),
                                        redis:RedisClient=Depends(get_redis),
                                        mongo:MongoDBClient=Depends(get_mongodb_client)):
    """
    买家商品库存统计
    获取库存统计数据，包括库存不足商品数量、正常商品数量、总库存量和商品种类数
    """
    verify_duter_token = VerifyDuterToken(token, redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool
    
    if not token_data:
        return {'code': 401, 'msg': 'Token无效或已过期', 'current': False}
    
    async def execute():
        try:
            # 获取所有商品ID
            sql_commodity_info = await sql.execute_query(
                '''SELECT shopping_id 
                  FROM shopping 
                  WHERE mall_id = %s AND audit = 1''',
                (stroe_id,)
            )
            
            if not sql_commodity_info:
                return {
                    'code': 200,
                    'msg': '暂无商品数据',
                    'success': True,
                    'data': {
                        'low_stock_count': 0,
                        'normal_stock_count': 0,
                        'total_inventory': 0,
                        'total_products': 0
                    }
                }
            
            shopping_ids = [item[0] for item in sql_commodity_info]
            placeholders = ','.join(['%s'] * len(shopping_ids))
            
            # 获取所有规格信息
            sql_specification_info = await sql.execute_query(
                f'''SELECT shopping_id, stock, minimum_balance 
                    FROM specification 
                    WHERE mall_id = %s AND shopping_id IN ({placeholders})''',
                (stroe_id, *shopping_ids)
            )
            
            low_stock_count = 0  # 库存不足的商品数
            normal_stock_count = 0  # 正常库存商品数
            total_inventory = 0  # 总库存量
            product_counts = {}  # 记录每个商品的库存状态
            
            for spec in sql_specification_info:
                shopping_id = spec[0]
                stock = spec[1] or 0
                minimum_balance = spec[2] or 0
                total_inventory += stock
                
                # 判断是否为低库存商品
                if stock <= minimum_balance:
                    if shopping_id not in product_counts or product_counts[shopping_id] != 'normal':
                        product_counts[shopping_id] = 'low'
                else:
                    product_counts[shopping_id] = 'normal'
            
            # 统计各类商品数量
            low_stock_count = sum(1 for status in product_counts.values() if status == 'low')
            normal_stock_count = sum(1 for status in product_counts.values() if status == 'normal')
            
            result = {
                'code': 200,
                'msg': '获取库存统计成功',
                'success': True,
                'data': {
                    'low_stock_count': low_stock_count,      # 库存不足商品数量
                    'normal_stock_count': normal_stock_count,  # 正常库存商品数量
                    'total_inventory': total_inventory,      # 总库存量
                    'total_products': len(product_counts)     # 商品种类总数
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取库存统计失败: {str(e)}")
            return {'code': 500, 'msg': f'服务器错误: {str(e)}', 'success': False}
    
    if token_data.get('station') == '1':
        sql_data = await sql.execute_query('select user from seller_sing where user = %s',(token_data.get('user'),))
        if not sql_data:
            return {'code': 403, 'msg': '商家用户不存在', 'current': False}
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            if stroe_id not in token_data.get('state_id_list'):
                return {'code': 403, 'msg': '您没有权限操作该店铺的库存统计', 'current': False}
            return await execute()
        else:
            return {'code': 403, 'msg': 'Token验证失败', 'current': False}
    else:
        role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                      db=db,
                                                      redis=redis,
                                                      name=token_data.get('user'),
                                                      mall_id=token_data.get('mall_id'))
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        if not role_authority or len(role_authority) == 0 or len(role_authority[0]) == 0:
            return {'code': 403, 'msg': '权限验证失败', 'current': False}
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await sql.execute_query('select user from store_user where user = %s and store_id = %s',
                                          (token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code and len(execute_code) > 2 and execute_code[2] and verify_data[0]:
            if stroe_id != token_data.get('mall_id'):
                return {'code': 403, 'msg': '您没有权限操作该店铺的库存统计', 'current': False}
            return await execute()
        else:
            return {'code': 403, 'msg': '您没有权限执行此操作', 'current': False}