from aiomysql import Connection

from fastapi import APIRouter,Query,Depends

from services.buyer_role_authority import RoleAuthorityService
from data.mongodb_client import MongoDBClient,get_mongodb_client


router = APIRouter()

@router.get('/cs')
async def get_cs(data:int=Query(...,description='角色id'), mongodb: MongoDBClient = Depends(get_mongodb_client)):
    try:
        # 插入数据（示例）
        await mongodb.insert_one('commodity_msg',{'id':1,'name':'商品1','price':100})
        
        # 读取数据 - 方法1：查询单个文档
        single_doc = await mongodb.find_one('commodity_msg', {'id': 1})
        
        # 读取数据 - 方法2：查询多个文档
        all_docs = await mongodb.find_many('commodity_msg', {})
        
        # 读取数据 - 方法3：带条件的查询
        filtered_docs = await mongodb.find_many('commodity_msg', {'price': {'$gte': 50}})
        
        # 读取数据 - 方法4：分页查询
        paged_docs = await mongodb.find_many(
            'commodity_msg', 
            {}, 
            skip=0, 
            limit=10, 
            sort=[('price', -1)]  # 按价格降序排列
        )
        
        # 读取数据 - 方法5：统计文档数量
        total_count = await mongodb.count_documents('commodity_msg', {})
        
        # 确保返回的数据是可JSON序列化的
        return {
            'single_document': single_doc,
            'all_documents': all_docs,
            'filtered_documents': filtered_docs,
            'paged_documents': paged_docs,
            'total_count': total_count,
            'message': '数据读取成功',
            'status': 'success'
        }
    except Exception as e:
        return {
            'error': str(e),
            'status': 'error',
            'message': '数据读取失败'
        }

@router.get('/cs/advanced')
async def get_cs_advanced(mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """高级查询示例"""
    try:
        # 复杂条件查询
        complex_query = {
            '$and': [
                {'price': {'$gte': 50}},
                {'price': {'$lte': 500}},
                {'name': {'$regex': '商品'}}  # 模糊匹配
            ]
        }
        
        complex_results = await mongodb.find_many('commodity_msg', complex_query)
        
        # 简单统计（不使用聚合管道）
        high_price_count = await mongodb.count_documents('commodity_msg', {'price': {'$gte': 100}})
        low_price_count = await mongodb.count_documents('commodity_msg', {'price': {'$lt': 100}})
        
        return {
            'complex_query_results': complex_results,
            'statistics': {
                'high_price_count': high_price_count,
                'low_price_count': low_price_count,
                'total_with_complex_conditions': len(complex_results)
            },
            'status': 'success'
        }
    except Exception as e:
        return {
            'error': str(e),
            'status': 'error',
            'message': '高级查询失败'
        }