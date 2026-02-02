from typing import Annotated
from datetime import date, datetime, timedelta
import asyncio
import jwt
from base64 import b64encode

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken
from services.cache_service import CacheService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import AddMallData

router = APIRouter()

@router.post("/add_mall")
async def add_mall(data:Annotated[AddMallData,Form()],db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
    """
    管理员添加店铺
    """
    verify_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_token.token_data()
    sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
    verity_val = await verify_token.verify_token(sql_data=sql_data)
    if verity_val[0]:
        if verity_val[1] != 'admin':
            return {'msg':'权限不足','current':False}
        elif verity_val[1] == 'admin':
            sql_user_admin = await execute_db_query(db,"select user from seller_sing where user = %s",(data.user))
            if not sql_user_admin:
                return {'msg':'选择的用户没有店长账号不能设置为店长,','current':False,'code':200}
            
            await execute_db_query(db,
                                   'INSERT INTO store (mall_name,user,mall_phone,mall_site,mall_describe,creation_time,state) values (%s,%s,%s,%s,%s,%s,%s)',
                                   (data.mall_name,data.user,data.mall_phone,data.mall_site,data.info,date.today(),1))
            sql_prod_id = await execute_db_query(db,'SELECT LAST_INSERT_ID() AS prod_id;')
            prod_id = sql_prod_id[0][0]
            
            cache = CacheService(redis)
            await cache.delete_pattern(f'mall_name:user:{data.user}')
            
            try:
                sql_user_data = await execute_db_query(db,'select * from seller_sing where user = %s',(data.user))
                await execute_db_query(db,'update mall_info set mall_number = mall_number+1 where user = %s',(data.user))
                if not sql_user_data:
                    await cache.delete_pattern(f'admin:mall:info:{data.user}')
                    return {'msg':'添加成功','prod_id':prod_id,'current':True,'code':200}

                state = await execute_db_query(db,"select mall_state from mall_info where user = %s",(data.user,))
                if not state or state[0][0] != 1:
                    await cache.delete_pattern(f'admin:mall:info:{data.user}')
                    return {'msg':'添加成功','prod_id':prod_id,'current':True,'code':200}
                

                mall_id = await execute_db_query(db,'select mall_id from store where user = %s',(data.user))
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
                
                old_expire = await redis.get(f'buyer_{data.user}')
                
                await redis.set(f'buyer_{data.user}', expire_timestamp)
                
                async def delete_old_token():
                    await asyncio.sleep(10)
                    try:
                        current_expire = await redis.get(f'buyer_{data.user}')
                        if old_expire and current_expire and str(current_expire) == str(old_expire):
                            await redis.delete(f'buyer_{data.user}')
                    except Exception as e:
                        pass
                
                asyncio.create_task(delete_old_token())
                
                return {
                    'msg': '添加成功',
                    'prod_id': prod_id,
                    'current': True,
                    'code': 200,
                    'token': new_token,
                    'token_type': 'bearer'
                }
            except Exception as e:
                return {'msg':'添加成功','prod_id':prod_id,'current':True,'code':200}
        else:
            return {'msg':'权限不足','current':False,'code':403}
    else:
        return {'msg':'token验证失败','current':False,'code':401}