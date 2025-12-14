from base64 import b64encode
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
            state = await execute_db_query(db,
                                           "select mall_state from mall_info where user = %s",(data.user,))
            if sql_data and state[0][0] == 1:
                payload = {
                        'user': sql_data[0][0],
                        'station':data.station,
                        'role':-1,
                        "state":state[0][0],
                        'exp':str(expire_timestamp)
                    }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                info = {"user":sql_data[0][0]}
                print(sql_data[0][2])
                with open(sql_data[0][2] if sql_data[0][2] else './buyer_use_img/通用/通用.png', "rb") as image_file:
                    encoded_string = b64encode(image_file.read()).decode('utf-8')
                    info['img'] = encoded_string



                
                await redis.set(f'buyer_{data.user}',expire_timestamp)


                return {'msg':'token生成成功','token':token,"token_type": "bearer",'current':True,'info':info}
            else:
                return {'msg':'用户名或密码错误','current':False}



        elif data.station == '2':

            sel_data = await execute_db_query(db,'select * from store_user where user = %s and (password = %s and store_id = %s)',(data.user,data.password,data.mall_id))
            if sel_data and sel_data[0][6] == 1:
                payload = {
                        'user': sel_data[0][1],
                        'station':data.station,
                        'role':sel_data[0][3],
                        'mall_id':sel_data[0][0],
                        "state":sel_data[0][6],
                        'exp':str(expire_timestamp)
                    }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                expire_timestamp = int(expire.timestamp())
                info = {"user":sel_data[0][1]}
                print(info)
                with open(sel_data[0][5] if sel_data[0][5] else './buyer_use_img/通用/通用.png', "rb") as image_file:
                    encoded_string = b64encode(image_file.read()).decode('utf-8')
                    info['img'] = encoded_string
                await redis.set(f'buyer_{sel_data[0][0]}_{data.user}',expire_timestamp)
                return {'msg':'token生成成功','token':token,"token_type": "bearer",'current':True,'info':info}
            else:
                return {'msg':'用户名或密码错误','current':False}


        else:
            return {'msg':'用户名或密码错误','current':False}
    except Exception as e:
        return {'msg':e,'current':False}

