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
    """
    商户端登录Token生成接口
    - station='1': 主商户登录（可管理多个店铺，role=-1表示超级管理员）
    - station='2': 店铺用户登录（只能管理指定店铺，role为具体角色ID）
    """
    SECRET_KEY = "$@?%^159ASx"
    expire_minutes = 7
    expire = datetime.utcnow() + timedelta(days=expire_minutes)
    expire_timestamp = int(expire.timestamp())

    try:
        # 主商户登录逻辑
        if data.station == '1':
            sql_data = await execute_db_query(db,'select * from seller_sing where user = %s and password = %s',(data.user,data.password))
            state = await execute_db_query(db,
                                           "select mall_state from mall_info where user = %s",(data.user,))
            # 验证账号存在且店铺状态正常（state=1）
            if sql_data and state[0][0] == 1:
                # 获取该商户管理的所有店铺ID列表
                mall_id = await execute_db_query(db,'select mall_id from store where user = %s',(data.user))
                mall_id_list = [i[0]for i in mall_id]
                payload = {
                        'user': sql_data[0][0],
                        'station':data.station,
                        'role':-1,  # -1表示主商户（超级管理员）
                        "state":state[0][0],
                        'state_id_list':mall_id_list,  # 可管理的店铺列表
                        'exp':str(expire_timestamp)
                    }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                info = {"user":sql_data[0][0]}
                # 将用户头像转为Base64编码
                with open(sql_data[0][2] if sql_data[0][2] else './buyer_use_img/通用/通用.png', "rb") as image_file:
                    encoded_string = b64encode(image_file.read()).decode('utf-8')
                    info['img'] = encoded_string
                
                # 将Token过期时间存入Redis，用于后续验证
                await redis.set(f'buyer_{data.user}',expire_timestamp)

                return {'msg':'token生成成功','token':token,"token_type": "bearer",'current':True,'info':info}
            else:
                return {'msg':'用户名或密码错误','current':False}

        # 店铺用户登录逻辑
        elif data.station == '2':
            sel_data = await execute_db_query(db,'select * from store_user where user = %s and (password = %s and store_id = %s)',(data.user,data.password,data.mall_id))
            # 验证账号存在且用户状态正常（state=1）
            if sel_data and sel_data[0][6] == 1:
                payload = {
                        'user': sel_data[0][1],
                        'station':data.station,
                        'role':sel_data[0][3],  # 具体角色ID
                        'mall_id':sel_data[0][0],  # 只能管理该店铺
                        "state":sel_data[0][6],
                        'exp':str(expire_timestamp)
                    }
                token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
                expire_timestamp = int(expire.timestamp())
                info = {"user":sel_data[0][1]}
                # 将用户头像转为Base64编码
                with open(sel_data[0][5] if sel_data[0][5] else './buyer_use_img/通用/通用.png', "rb") as image_file:
                    encoded_string = b64encode(image_file.read()).decode('utf-8')
                    info['img'] = encoded_string
                # Redis键格式：buyer_{店铺ID}_{用户名}，用于区分不同店铺的用户
                await redis.set(f'buyer_{sel_data[0][0]}_{data.user}',expire_timestamp)
                return {'msg':'token生成成功','token':token,"token_type": "bearer",'current':True,'info':info}
            else:
                return {'msg':'用户名或密码错误','current':False}

        else:
            return {'msg':'用户名或密码错误','current':False}
    except Exception as e:
        return {'msg':e,'current':False}

