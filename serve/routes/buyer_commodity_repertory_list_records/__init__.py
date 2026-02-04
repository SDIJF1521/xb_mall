from typing import Annotated
import logging
from datetime import datetime

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form, HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import CommodityRepertoryRecord
from data.sql_client_pool import get_db_pool, db_pool
from data.redis_client import get_redis, RedisClient
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post('/buyer_commodity_repertory_list_records')
async def get_commodity_repertory_records(
    data: Annotated[CommodityRepertoryRecord, Form(...)],
    db: Connection = Depends(get_db_pool),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client)
):
    '''
    获取商品库存变更记录
    支持按时间范围、变更类型等条件筛选，提供分页功能
    '''
    verify_duter_token = VerifyDuterToken(data.token, redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool

    if not token_data:
        return {'code': 401, 'msg': 'Token无效或已过期', 'current': False}

    async def execute():
        try:
            cache = CacheService(redis)
            
            cache_key = cache._make_key(
                'commodity:repertory:records',
                data.stroe_id,
                data.shopping_id,
                data.sku_id,
                data.change_type,
                data.start_time,
                data.end_time,
                data.page
            )
            
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug(f"从缓存获取库存记录: {cache_key}")
                return cached_data

            query_filter = {
                'mall_id': data.stroe_id,
                'shopping_id': data.shopping_id,
                'specification_id': data.sku_id
            }
            
            if data.start_time or data.end_time:
                time_filter = {}
                if data.start_time:
                    time_filter['$gte'] = data.start_time
                if data.end_time:
                    time_filter['$lte'] = data.end_time
                query_filter['time'] = time_filter
            
            if data.change_type:
                query_filter['change_type'] = data.change_type

            skip = (data.page - 1) * data.page_size
            
            total_count = await mongodb.count_documents('inventory_records', query_filter)
            
            if total_count == 0:
                result = {
                    'code': 200,
                    'msg': '暂无库存变更记录',
                    'current': True,
                    'success': True,
                    'data': {
                        'items': [],
                        'total': 0,
                        'page': data.page,
                        'page_size': data.page_size,
                        'total_pages': 0
                    }
                }
                await cache.set(cache_key, result, expire=300)
                return result

            mongodb_data = await mongodb.find_many(
                'inventory_records',
                query_filter,
                sort=[('time', -1)], 
                skip=skip,
                limit=data.page_size
            )

            if mongodb_data:
                commodity_info = await mongodb.find_one('shopping', {
                    'mall_id': data.stroe_id,
                    'shopping_id': data.shopping_id
                })
                
                commodity_name = commodity_info.get('name', '未知商品') if commodity_info else '未知商品'
                

                current_stock_info = await sql.execute_query(
                    'SELECT stock FROM specification WHERE mall_id = %s AND shopping_id = %s AND specification_id = %s',
                    (data.stroe_id, data.shopping_id, data.sku_id)
                )
                current_stock = current_stock_info[0][0] if current_stock_info else 0
                
                formatted_records = []
                running_stock = current_stock  # 从当前库存开始，逆向计算
                
                for record in mongodb_data:
                    change_num = record.get('change_num', 0)
                    change_type = record.get('change_type', '')
                    
                    if change_type == '增加':
                        after_stock = running_stock
                        before_stock = running_stock - change_num
                        running_stock = before_stock  # 更新运行库存
                    elif change_type == '减少':
                        after_stock = running_stock
                        before_stock = running_stock + change_num
                        running_stock = before_stock  # 更新运行库存
                    else:  # 设置
                        after_stock = change_num
                        before_stock = running_stock  # 保持之前的库存状态
                        running_stock = change_num  # 更新运行库存
                    
                    formatted_record = {
                        'id': str(record.get('_id', '')),
                        'createTime': record.get('time', ''),
                        'type': change_type,
                        'changeAmount': change_num,
                        'beforeStock': before_stock,
                        'afterStock': after_stock,
                        'operator': record.get('user', ''),
                        'remark': record.get('info', '') if record.get('info') != 'null' else ''
                    }
                    formatted_records.append(formatted_record)

                total_pages = (total_count + data.page_size - 1) // data.page_size

                result = {
                    'code': 200,
                    'msg': '查询成功',
                    'current': True,
                    'success': True,
                    'data': {
                        'items': formatted_records,
                        'total': total_count,
                        'page': data.page,
                        'page_size': data.page_size,
                        'total_pages': total_pages
                    }
                }
                
                expire_time = 300 if (data.change_type or data.start_time or data.end_time) else 600
                await cache.set(cache_key, result, expire=expire_time)
                
                logger.info(f"查询库存记录成功: 店铺{data.stroe_id}, 商品{data.shopping_id}, 规格{data.sku_id}, 共{total_count}条记录")
                return result
            else:
                result = {
                    'code': 200,
                    'msg': '暂无库存变更记录',
                    'current': True,
                    'success': True,
                    'data': {
                        'items': [],
                        'total': 0,
                        'page': data.page,
                        'page_size': data.page_size,
                        'total_pages': 0
                    }
                }
                await cache.set(cache_key, result, expire=300)
                return result

        except Exception as e:
            logger.error(f"查询库存记录失败: {str(e)}")
            return {'code': 500, 'msg': f'服务器错误: {str(e)}', 'current': False}

    if token_data.get('station') == '1':
        sql_data = await sql.execute_query(
            'select user from seller_sing where user = %s',
            (token_data.get('user'),)
        )
        if not sql_data:
            return {'code': 403, 'msg': '商家用户不存在', 'current': False}
        
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data[0]:
            if data.stroe_id not in token_data.get('state_id_list', []):
                return {'code': 403, 'msg': '您没有权限查看该店铺的库存记录', 'current': False}
            return await execute()
        else:
            return {'code': 403, 'msg': 'Token验证失败', 'current': False}
    else:
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
            if token_data.get('mall_id') != data.stroe_id:
                return {'code': 403, 'msg': '您没有权限查看该店铺的库存记录', 'current': False}
            return await execute()
        else:
            return {'code': 403, 'msg': '您没有权限查看库存记录', 'current': False}