import os
import asyncio
import jwt
from typing import Annotated
from datetime import datetime, timedelta

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form

from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db,execute_db_query
from data.data_mods import DeleteMall

router = APIRouter()


@router.delete('/buyer_delete_mall')
async def buyer_delete_mall(data: Annotated[DeleteMall, Form()], db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):
    """主商户删除店铺"""
    try:
        verifier = VerifyDuterToken(data.token,redis)
        token_data = await verifier.token_data()
        
        if not token_data:
            return {'msg':'Token无效或已过期','current':False}
        
        if token_data.get('station') == '1':
            sql_data_store_id = await execute_db_query(db,"select mall_id from store where mall_id = %s",(data.mall_id))
            if not sql_data_store_id:
                return {'msg':'该店铺不存在或无权限删除','current':False}
            
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            img_path = await execute_db_query(db,"select img_path from store where mall_id = %s",(data.mall_id))
            if sql_data:
                cache = CacheService(redis)
                user_name = token_data.get('user')
                await execute_db_query(db,'delete from store where mall_id = %s',(data.mall_id))
                if img_path and img_path[0][0]:
                    img_path_str = img_path[0][0]
                    try:
                        if os.path.exists(img_path_str):
                            os.remove(img_path_str)
                        img_cache_key = cache._make_key('img_base64', img_path_str)
                        await cache.delete(img_cache_key)
                    except Exception:
                        pass
                await cache.delete(cache._make_key('mall_info', data.mall_id))
                await cache.delete_pattern(f'mall_name:user:{user_name}')
                await cache.delete_pattern(f'mall_name:mall:{data.mall_id}')
                await cache.delete_pattern(f'mall_info:user:{user_name}')
                await cache.delete_pattern(f'admin:mall:info:%d'%(data.mall_id))
                
                try:
                    sql_user_data = await execute_db_query(db,'select * from seller_sing where user = %s',(token_data.get('user')))
                    if not sql_user_data:
                        return {'msg':'删除成功','current':True,'code':200}
                    
                    state = await execute_db_query(db,"select mall_state from mall_info where user = %s",(token_data.get('user'),))
                    if not state or state[0][0] != 1:
                        return {'msg':'删除成功','current':True,'code':200}
                    
                    mall_id = await execute_db_query(db,'select mall_id from store where user = %s',(token_data.get('user')))
                    mall_id_list = [i[0] for i in mall_id]
                    
                    SECRET_KEY = "$@?%^159ASx"
                    expire_minutes = 7
                    expire = datetime.utcnow() + timedelta(days=expire_minutes)
                    expire_timestamp = int(expire.timestamp())
                    
                    payload = {
                        'user': sql_user_data[0][0],
                        'station': '1',
                        'role': -1,
                        "state": state[0][0],
                        'state_id_list': mall_id_list,
                        'exp': str(expire_timestamp)
                    }
                    new_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                    
                    old_expire = await redis.get(f'buyer_{token_data.get("user")}')
                    
                    await redis.set(f'buyer_{token_data.get("user")}', expire_timestamp)
                    
                    async def delete_old_token():
                        await asyncio.sleep(10)
                        try:
                            current_expire = await redis.get(f'buyer_{token_data.get("user")}')
                            if old_expire and current_expire and str(current_expire) == str(old_expire):
                                await redis.delete(f'buyer_{token_data.get("user")}')
                        except Exception as e:
                            pass
                    
                    asyncio.create_task(delete_old_token())
                    
                    return {
                        'msg': '删除成功',
                        'current': True,
                        'code': 200,
                        'token': new_token,
                        'token_type': 'bearer'
                    }
                except Exception as e:
                    return {'msg':'删除成功','current':True,'code':200}
            else:
                return {'msg':'删除失败','current':False}
        else:
            return {'msg':'token 验证失败','current':False}
    except Exception as e:
        return {'error':str(e),'current':False}