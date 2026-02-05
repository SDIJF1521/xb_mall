from typing import Annotated
import logging

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import CommodityRepertoryAllModel
from data.sql_client_pool import get_db_pool, db_pool
from data.redis_client import get_redis,RedisClient
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/buyer_commodity_repertory_all")
async def get_commodity_repertory_all(
    data:Annotated[CommodityRepertoryAllModel,Form(...)],
    db:Connection = Depends(get_db_pool),
    redis:RedisClient = Depends(get_redis),
    mongodb:MongoDBClient = Depends(get_mongodb_client)
):
    '''获取店铺所有商品库存信息'''
    verify_duter_token = VerifyDuterToken(data.token, redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool

    async def execute():
        try:
            # 获取店铺所有商品的基本信息和规格信息
            cache = CacheService(redis)
            cache_key = cache._make_key('commodity:repertory:all', data.stroe_id)
            cached_data = await cache.get(cache_key)
            if cached_data:
                return cached_data

            # 获取所有已审核的商品
            sql_commodity_info = await sql.execute_query(
                '''SELECT shopping_id, classify_categorize, time, audit 
                  FROM shopping 
                  WHERE mall_id = %s AND audit = 1 
                  ORDER BY shopping_id DESC''',
                (data.stroe_id,)
            )
            
            if not sql_commodity_info:
                result = {
                    'code': 200,
                    'msg': '暂无数据',
                    'success': True,
                    'data': [],
                    'total': 0
                }
                return result

            # 获取所有商品的规格信息
            shopping_ids = [item[0] for item in sql_commodity_info]
            placeholders = ','.join(['%s'] * len(shopping_ids))
            
            sql_specification_info = await sql.execute_query(
                f'''SELECT shopping_id, specification_id, price, stock, maximum_inventory, minimum_balance, time 
                    FROM specification 
                    WHERE mall_id = %s AND shopping_id IN ({placeholders})''',
                (data.stroe_id, *shopping_ids)
            )
            
            if not sql_specification_info:
                result = {
                    'code': 200,
                    'msg': '暂无规格数据',
                    'success': True,
                    'data': [],
                    'total': 0
                }
                return result

            # 获取MongoDB中的商品信息
            mongodb_filter = {
                'mall_id': data.stroe_id,
                'shopping_id': {'$in': shopping_ids}
            }
            mongodb_data = await mongodb.find_many('shopping', mongodb_filter)
            mongodb_dic = {item['shopping_id']: item for item in mongodb_data}

            # 处理规格数据，计算库存状态
            spec_dic = {}
            for spec in sql_specification_info:
                shopping_id = spec[0]
                if shopping_id not in spec_dic:
                    spec_dic[shopping_id] = []
                
                spec_info = {
                    'specification_id': spec[1],
                    'price': float(spec[2]) if spec[2] else 0.0,
                    'stock': int(spec[3]) if spec[3] else 0,
                    'maximum_inventory': int(spec[4]) if spec[4] else 0,
                    'minimum_balance': int(spec[5]) if spec[5] else 0,
                    'time': spec[6].strftime('%Y-%m-%d') if spec[6] else ''
                }
                
                # 计算库存状态
                if spec_info['stock'] <= 0:
                    stock_status = '缺货'
                elif spec_info['stock'] <= spec_info['minimum_balance']:
                    stock_status = '库存不足'
                elif spec_info['stock'] <= spec_info['minimum_balance'] * 2:
                    stock_status = '库存较低'
                else:
                    stock_status = '库存充足'
                spec_info['stock_status'] = stock_status
                spec_dic[shopping_id].append(spec_info)

            # 构建最终结果
            result_data = []
            for commodity in sql_commodity_info:
                shopping_id = commodity[0]
                mongodb_info = mongodb_dic.get(shopping_id, {})
                specifications = spec_dic.get(shopping_id, [])
                
                if not specifications:
                    continue
                
                # 计算总库存
                total_stock = sum(spec['stock'] for spec in specifications)
                
                # 获取最新时间
                spec_times = [spec['time'] for spec in specifications if spec.get('time')]
                commodity_time = max(spec_times) if spec_times else (commodity[2].strftime('%Y-%m-%d') if commodity[2] else '')
                
                item = {
                    'shopping_id': shopping_id,
                    'name': mongodb_info.get('name', ''),
                    'classify_categorize': commodity[1],
                    'time': commodity_time,
                    'audit': commodity[3] if len(commodity) > 3 else 0,
                    'total_stock': total_stock,
                    'specifications': specifications
                }
                result_data.append(item)

            result = {
                'code': 200,
                'msg': '获取成功',
                'success': True,
                'data': result_data,
                'total': len(result_data)
            }
            
            # 设置缓存，有效期5分钟
            try:
                await cache.set(cache_key, result, expire=300)
                logger.debug(f"缓存已设置 | Key: {cache_key} | Expire: 300s")
            except Exception as e:
                logger.error(f"缓存设置异常 | Key: {cache_key} | 错误: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"获取商品库存信息失败: {str(e)}")
            return {'code': 500, 'msg': f'服务器错误: {str(e)}', 'success': False}

    if not token_data:
        return {'code': 401, 'msg': 'Token无效或已过期', 'current': False}
    
    if token_data.get('station') == '1':
        # 商家用户权限验证
        sql_data = await sql.execute_query('select user from seller_sing where user = %s', (token_data.get('user'),))
        if not sql_data:
            return {'code': 403, 'msg': '商家用户不存在', 'current': False}
        
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data[0]:
            if data.stroe_id not in token_data.get('state_id_list', []):
                return {'code': 403, 'msg': '您没有权限查看该店铺的库存信息', 'current': False}
            return await execute()
        else:
            return {'code': 403, 'msg': 'Token验证失败', 'current': False}
    else:
        # 店铺用户权限验证
        role_authority_service = RoleAuthorityService(
            role=token_data.get('role'),
            db=db,
            redis=redis,
            name=token_data.get('user'),
            mall_id=token_data.get('mall_id')
        )
        
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        if not role_authority or len(role_authority) == 0 or len(role_authority[0]) == 0:
            return {'code': 403, 'msg': '权限验证失败', 'current': False}
        
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await sql.execute_query(
            'select user from store_user where user = %s and store_id = %s',
            (token_data.get('user'), token_data.get('mall_id'))
        )
        verify_data = await verify_duter_token.verify_token(sql_data)
        
        if execute_code and len(execute_code) > 2 and execute_code[2] and verify_data[0]:
            if data.stroe_id != token_data.get('mall_id'):
                return {'code': 403, 'msg': '您没有权限查看该店铺的库存信息', 'current': False}
            return await execute()
        else:
            return {'code': 403, 'msg': '您没有权限查看该店铺的库存信息', 'current': False}