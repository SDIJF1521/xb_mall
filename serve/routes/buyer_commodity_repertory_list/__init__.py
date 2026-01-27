from typing import Annotated, Optional
import logging

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerCommodityRepertoryList
from data.sql_client_pool import get_db_pool, db_pool
from data.redis_client import get_redis,RedisClient
from data.mongodb_client import get_mongodb_client,MongoDBClient

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/buyer_commodity_repertory_list")
async def buyer_commodity_repertory_list(
                                        data:Annotated[BuyerCommodityRepertoryList,Form()],
                                        db:Connection=Depends(get_db_pool),
                                        redis:RedisClient=Depends(get_redis),
                                        mongo:MongoDBClient=Depends(get_mongodb_client)):
    """
    买家商品库存列表
    获取商品库存信息，包括规格、价格、库存数量、最大库存和最小余额
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool
    
    if not token_data:
        return {'code':401,'msg':'Token无效或已过期','current':False}
    
    async def execute():
        try:
            offset = (data.page - 1) * data.page_size
            
            cache = CacheService(redis)
            cache_key = None
            
            if data.select and data.select.strip():
                # 搜索模式 - 支持按ID和名称模糊查询，同时考虑库存状态筛选
                search_pattern = data.select.strip()
                # 注意：缓存键包含了stock_status，确保不同库存状态的搜索结果不会互相干扰
                cache_key = cache._make_key('commodity:repertory:search', data.stroe_id, search_pattern, data.stock_status, data.page)
                cached_data = await cache.get(cache_key)
                if cached_data:
                    return cached_data
                
                try:
                    search_id = int(search_pattern)
                    sql_search_results = await sql.execute_query(
                        '''SELECT shopping_id FROM shopping 
                           WHERE mall_id = %s AND shopping_id = %s''',
                        (data.stroe_id, search_id)
                    )
                    id_matching_shopping_ids = [row[0] for row in sql_search_results]
                except ValueError:
                    id_matching_shopping_ids = []
                
                mongodb_filter = {
                    'mall_id': data.stroe_id,
                    'name': {'$regex': search_pattern, '$options': 'i'}
                }
                mongodb_commoidt_info = await mongo.find_many('shopping', mongodb_filter)
                
                all_matching_shopping_ids = set(id_matching_shopping_ids)
                all_matching_shopping_ids.update([item['shopping_id'] for item in mongodb_commoidt_info])
                all_matching_shopping_ids = list(all_matching_shopping_ids)
                
                if all_matching_shopping_ids:
                    placeholders_all = ','.join(['%s'] * len(all_matching_shopping_ids))
                    sql_specification_info_all = await sql.execute_query(
                        f'''SELECT shopping_id, specification_id, price, stock, maximum_inventory, minimum_balance 
                            FROM specification 
                            WHERE mall_id = %s AND shopping_id IN ({placeholders_all})''',
                        (data.stroe_id, *all_matching_shopping_ids)
                    )
                    
                    spec_dic_all = {}
                    for spec in sql_specification_info_all:
                        shopping_id = spec[0]
                        if shopping_id not in spec_dic_all:
                            spec_dic_all[shopping_id] = []
                        spec_info = {
                            'specification_id': spec[1],
                            'price': float(spec[2]) if spec[2] else 0.0,
                            'stock': int(spec[3]) if spec[3] else 0,
                            'maximum_inventory': int(spec[4]) if spec[4] else 0,
                            'minimum_balance': int(spec[5]) if spec[5] else 0
                        }
                        if spec_info['stock'] <= 0:
                            stock_status = '缺货'
                        elif spec_info['stock'] <= spec_info['minimum_balance']:
                            stock_status = '库存不足'
                        elif spec_info['stock'] <= spec_info['minimum_balance'] * 2:
                            stock_status = '库存较低'
                        else:
                            stock_status = '库存充足'
                        spec_info['stock_status'] = stock_status
                        spec_dic_all[shopping_id].append(spec_info)
                    
                    if data.stock_status:
                        matching_shopping_ids = [
                            shopping_id for shopping_id, specs in spec_dic_all.items()
                            if any(spec['stock_status'] == data.stock_status for spec in specs)
                        ]
                    else:
                        matching_shopping_ids = all_matching_shopping_ids
                    
                    total_count = len(matching_shopping_ids)
                    paginated_shopping_ids = matching_shopping_ids[offset:offset + data.page_size]
                    
                    if paginated_shopping_ids:
                        placeholders = ','.join(['%s'] * len(paginated_shopping_ids))
                        
                        sql_commodity_info = await sql.execute_query(
                            f'''SELECT shopping_id, classify_categorize, time, audit 
                                FROM shopping 
                                WHERE mall_id = %s AND shopping_id IN ({placeholders})''',
                            (data.stroe_id, *paginated_shopping_ids)
                        )
                        
                        sql_specification_info = await sql.execute_query(
                            f'''SELECT shopping_id, specification_id, price, stock, maximum_inventory, minimum_balance 
                                FROM specification 
                                WHERE mall_id = %s AND shopping_id IN ({placeholders})''',
                            (data.stroe_id, *paginated_shopping_ids)
                        )
                    else:
                        sql_commodity_info = []
                        sql_specification_info = []
                        total_count = 0
                else:
                    sql_commodity_info = []
                    sql_specification_info = []
                    total_count = 0
            else:
                cache_key = cache._make_key('commodity:repertory:list', data.stroe_id, data.stock_status, data.page)
                cached_data = await cache.get(cache_key)
                if cached_data:
                    return cached_data
                
                if data.stock_status:
                    all_shopping_ids_result = await sql.execute_query(
                        '''SELECT shopping_id 
                          FROM shopping 
                          WHERE mall_id = %s AND audit = 1''',
                        (data.stroe_id,)
                    )
                    all_shopping_ids = [row[0] for row in all_shopping_ids_result]
                    
                    if all_shopping_ids:
                        placeholders_all = ','.join(['%s'] * len(all_shopping_ids))
                        sql_specification_info_all = await sql.execute_query(
                            f'''SELECT shopping_id, specification_id, price, stock, maximum_inventory, minimum_balance 
                                FROM specification 
                                WHERE mall_id = %s AND shopping_id IN ({placeholders_all})''',
                            (data.stroe_id, *all_shopping_ids)
                        )
                        
                        spec_dic_all = {}
                        for spec in sql_specification_info_all:
                            shopping_id = spec[0]
                            if shopping_id not in spec_dic_all:
                                spec_dic_all[shopping_id] = []
                            spec_info = {
                                'specification_id': spec[1],
                                'price': float(spec[2]) if spec[2] else 0.0,
                                'stock': int(spec[3]) if spec[3] else 0,
                                'maximum_inventory': int(spec[4]) if spec[4] else 0,
                                'minimum_balance': int(spec[5]) if spec[5] else 0
                            }
                            if spec_info['stock'] <= 0:
                                stock_status = '缺货'
                            elif spec_info['stock'] <= spec_info['minimum_balance']:
                                stock_status = '库存不足'
                            elif spec_info['stock'] <= spec_info['minimum_balance'] * 2:
                                stock_status = '库存较低'
                            else:
                                stock_status = '库存充足'
                            spec_info['stock_status'] = stock_status
                            spec_dic_all[shopping_id].append(spec_info)
                        
                        filtered_shopping_ids = [
                            shopping_id for shopping_id, specs in spec_dic_all.items()
                            if any(spec['stock_status'] == data.stock_status for spec in specs)
                        ]
                        
                        total_count = len(filtered_shopping_ids)
                        paginated_shopping_ids = filtered_shopping_ids[offset:offset + data.page_size]
                        
                        if paginated_shopping_ids:
                            placeholders = ','.join(['%s'] * len(paginated_shopping_ids))
                            sql_commodity_info = await sql.execute_query(
                                f'''SELECT shopping_id, classify_categorize, time, audit 
                                  FROM shopping 
                                  WHERE mall_id = %s AND audit = 1 AND shopping_id IN ({placeholders})
                                  ORDER BY shopping_id''',
                                (data.stroe_id, *paginated_shopping_ids)
                            )
                            
                            sql_specification_info = await sql.execute_query(
                                f'''SELECT shopping_id, specification_id, price, stock, maximum_inventory, minimum_balance 
                                    FROM specification 
                                    WHERE mall_id = %s AND shopping_id IN ({placeholders})''',
                                (data.stroe_id, *paginated_shopping_ids)
                            )
                        else:
                            sql_commodity_info = []
                            sql_specification_info = []
                            total_count = 0
                    else:
                        sql_commodity_info = []
                        sql_specification_info = []
                        total_count = 0
                else:
                    total_result = await sql.execute_query(
                        '''SELECT COUNT(DISTINCT s.shopping_id) 
                        FROM shopping s 
                        WHERE s.mall_id = %s AND s.audit = 1''',
                        (data.stroe_id,))
                    total_count = total_result[0][0] if total_result else 0
                    
                    sql_commodity_info = await sql.execute_query(
                        '''SELECT shopping_id, classify_categorize, time, audit 
                          FROM shopping 
                          WHERE mall_id = %s AND audit = 1 
                          ORDER BY shopping_id DESC 
                          LIMIT %s OFFSET %s''',
                        (data.stroe_id, data.page_size, offset)
                    )
                    
                    if sql_commodity_info:
                        shopping_ids = [item[0] for item in sql_commodity_info]
                        placeholders = ','.join(['%s'] * len(shopping_ids))
                        sql_specification_info = await sql.execute_query(
                            f'''SELECT shopping_id, specification_id, price, stock, maximum_inventory, minimum_balance 
                                FROM specification 
                                WHERE mall_id = %s AND shopping_id IN ({placeholders})''',
                            (data.stroe_id, *shopping_ids)
                        )
                    else:
                        sql_specification_info = []
            
            if sql_commodity_info and sql_specification_info:
                shopping_ids = [item[0] for item in sql_commodity_info]
                mongodb_filter = {
                    'mall_id': data.stroe_id,
                    'shopping_id': {'$in': shopping_ids}
                }
                mongodb_data = await mongo.find_many('shopping', mongodb_filter)
                mongodb_dic = {item['shopping_id']: item for item in mongodb_data}
                
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
                        'minimum_balance': int(spec[5]) if spec[5] else 0
                    }
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
                
                if data.stock_status:
                    filtered_spec_dic = {}
                    for shopping_id, specs in spec_dic.items():
                        filtered_specs = [spec for spec in specs if spec['stock_status'] == data.stock_status]
                        if filtered_specs:
                            filtered_spec_dic[shopping_id] = filtered_specs
                    spec_dic = filtered_spec_dic
                
                result_data = []
                for commodity in sql_commodity_info:
                    shopping_id = commodity[0]
                    if data.stock_status and shopping_id not in spec_dic:
                        continue
                    
                    mongodb_info = mongodb_dic.get(shopping_id, {})
                    
                    total_stock = sum(spec['stock'] for spec in spec_dic.get(shopping_id, []))
                    
                    item = {
                        'shopping_id': shopping_id,
                        'name': mongodb_info.get('name', ''),
                        'classify_categorize': commodity[1],
                        'time': commodity[2].strftime('%Y-%m-%d') if commodity[2] else '',
                        'audit': commodity[3] if len(commodity) > 3 else 0,
                        'total_stock': total_stock,
                        'specifications': spec_dic.get(shopping_id, [])
                    }
                    result_data.append(item)
                
                if data.stock_status:
                    total_count = len(result_data)
                
                result = {
                    'code': 200,
                    'msg': '获取成功',
                    'success': True,
                    'data': result_data,
                    'total': total_count,
                    'page': data.page,
                    'page_size': data.page_size
                }
            else:
                result = {
                    'code': 200,
                    'msg': '暂无数据',
                    'success': True,
                    'data': [],
                    'total': 0,
                    'page': data.page,
                    'page_size': data.page_size
                }
            
            if cache_key:
                expire = 60 if (data.select and data.select.strip()) else 300
                try:
                    await cache.set(cache_key, result, expire=expire)
                    logger.debug(f"缓存已设置 | Key: {cache_key} | Expire: {expire}s")
                except Exception as e:
                    logger.error(f"缓存设置异常 | Key: {cache_key} | 错误: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"获取商品库存列表失败: {str(e)}")
            return {'code': 500, 'msg': f'服务器错误: {str(e)}', 'success': False}
    
    if token_data.get('station') == '1':
        sql_data = await sql.execute_query('select user from seller_sing where user = %s',(token_data.get('user'),))
        if not sql_data:
            return {'code': 403, 'msg': '商家用户不存在', 'current': False}
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            return {'code': 403, 'msg': 'Token验证失败', 'current': False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        if not role_authority or len(role_authority) == 0 or len(role_authority[0]) == 0:
            return {'code': 403, 'msg': '权限验证失败', 'current': False}
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await sql.execute_query('select user from store_user where user = %s and store_id = %s',
                                          (token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code and len(execute_code) > 2 and execute_code[2] and verify_data:
            return await execute()
        else:
            return {'code': 403, 'msg': '您没有权限执行此操作', 'current': False}