from typing import Annotated
from datetime import datetime, timedelta

import jwt
from aiomysql import Connection
from fastapi import APIRouter,Form,Depends,HTTPException


from data.data_mods import SellerSignIn
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient




def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/buyer_side_token')

async def  DuyerSideToken(data: Annotated[SellerSignIn,Form()], db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):

    SECRET_KEY = "$@?%^159ASx"
    expire_minutes = 7
    expire = datetime.utcnow() + timedelta(days=expire_minutes)
    expire_timestamp = int(expire.timestamp())


    try:
        if data.station == '1':
            sql_data = await execute_db_query(db,'select * from seller_sing where user = %s and password = %s',(data.user,data.password))
            if sql_data:
                payload = {
                        'user': sql_data[0][0],
                        'station':data.station,
                        'role':-1,
                        'exp':str(expire_timestamp)
                    }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                
                await redis.set(f'buyer_{data.user}',expire_timestamp)


                return {'msg':'token生成成功','token':token,"token_type": "bearer",'current':True}
            else:
                return {'msg':'用户名或密码错误','current':False}



        elif data.station == '2':
            sel_data = await execute_db_query(db,'select * from store_user where user = %s and password = %s',(data.user,data.password))
            if sel_data:
                payload = {
                        'user': sel_data[0][0],
                        'station':data.station,
                        'role':sel_data[0][3],
                        'exp':str(expire_timestamp)
                    }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                expire_timestamp = int(expire.timestamp())
                await redis.set(f'buyer_{data.user}',expire_timestamp)
                return {'msg':'token生成成功','token':token,"token_type": "bearer",'current':True}
            else:
                return {'msg':'用户名或密码错误','current':False}


        else:
            return {'msg':'用户名或密码错误','current':False}
    except Exception as e:
        return {'msg':e,'current':False}

