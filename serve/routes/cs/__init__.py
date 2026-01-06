from aiomysql import Connection

from fastapi import APIRouter,Query,Depends

from services.buyer_role_authority import RoleAuthorityService
from data.mongodb_client import MongoDBClient,get_mongodb_client


router = APIRouter()

@router.get('/cs')
async def get_cs(data:int=Query(...,description='角色id'), mongodb: MongoDBClient = Depends(get_mongodb_client)):
    try:
        await mongodb.insert_one('commodity_msg',{'id':1,'name':'商品1','price':100})
        
        single_doc = await mongodb.find_one('commodity_msg', {'id': 1})
        
        all_docs = await mongodb.find_many('commodity_msg', {})
        
        filtered_docs = await mongodb.find_many('commodity_msg', {'price': {'$gte': 50}})
        
        paged_docs = await mongodb.find_many(
            'commodity_msg', 
            {}, 
            skip=0, 
            limit=10, 
            sort=[('price', -1)]
        )
        
        total_count = await mongodb.count_documents('commodity_msg', {})
        
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
        complex_query = {
            '$and': [
                {'price': {'$gte': 50}},
                {'price': {'$lte': 500}},
                {'name': {'$regex': '商品'}}
            ]
        }
        
        complex_results = await mongodb.find_many('commodity_msg', complex_query)
        
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