from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.get('/buyer_commodity_inform')
async def buyer_commodity_inform(access_token:str = Header(...),
                                db:Connection = Depends(get_db),
                                redis:RedisClient = Depends(get_redis),
                                mongodb:MongoDBClient = Depends(get_mongodb_client)):
    """
    获取商品审核通知
    返回：未读通知列表（包含商品名称、审核状态、审核消息等）
    """
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()
    
    if not token_data:
        return {'code':401,'msg':'Token无效或已过期','current':False}

    async def execute(id_list):
        cache = CacheService(redis)
        cache_key = cache._make_key('commodity:inform', ','.join(map(str, id_list)))
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data
        
        mongodb_data = []
        for i in id_list:
            mongodb_data.extend(await mongodb.find_many('commodity_msg',{'mall_id':i,'read':0}))

        if mongodb_data:
            result_data = []
            for msg in mongodb_data:
                commodity_info = await mongodb.find_one('shopping', {
                    'mall_id': msg.get('mall_id'),
                    'shopping_id': msg.get('shopping_id')
                })
                
                item = {
                    'mall_id': msg.get('mall_id'),
                    'shopping_id': msg.get('shopping_id'),
                    'pass': msg.get('pass'),
                    'read': msg.get('read'),
                    'name': commodity_info.get('name') if commodity_info else None,
                    'info': commodity_info.get('info') if commodity_info else None,
                    'msg': msg.get('msg'),
                    'auditor': msg.get('auditor')
                }
                result_data.append(item)
            
            result = {'code':200,'msg':'获取成功','current':True,'data':result_data,'flag':True}
            await cache.set(cache_key, result, expire=30)
            return result
        else:
            return {'code':200,'msg':'没有通知','current':True,'flag':False,'data':[]}

    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                mall_id_list = token_data.get('state_id_list', [])
                if not mall_id_list:
                    return {'code':200,'msg':'没有店铺','current':True,'flag':False,'data':[]}
                return await execute(mall_id_list)
            else:
                return {'code':403,'msg':'验证失败','current':False}
        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            if not role_authority or len(role_authority) == 0 or len(role_authority[0]) == 0:
                return {'code':403,'msg':'权限验证失败','current':False}
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if execute_code and len(execute_code) > 2 and execute_code[2] and verify_data:
                mall_id = token_data.get('mall_id')
                if not mall_id:
                    return {'code':200,'msg':'没有店铺信息','current':True,'flag':False,'data':[]}
                return await execute([mall_id])
            else:
                return {'code':403,'msg':'您没有权限执行此操作','current':False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))