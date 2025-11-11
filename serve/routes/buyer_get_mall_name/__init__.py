from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import GetMallName


router = APIRouter()


    
@router.post('/get_mall_name')
async def buyer_get_mall_name(data:Annotated[GetMallName,Form()] ,db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):
    try:
        # 验证 token
        verify_duter_token = VerifyDuterToken(data.token,redis)
        token_data = await verify_duter_token.token_data()
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            mall_name = []
            if data.mall_name is None:
                if verify_data:
                    sql_data = await execute_db_query(db,'select mall_id,mall_name,creation_time from store where user = %s',(token_data.get('user')))
                    if sql_data:
                        print(2)
                        print(sql_data)
                        for i in sql_data:
                            mall_name.append({'id':i[0],'mall_name':i[1],'creation_time':i[2]})
                    return {'mall_name':mall_name,'current':True}
                else:
                    return {'error':'token 验证失败','current':False}
            else:
                sql_data = await execute_db_query(db,'select mall_id,mall_name,creation_time from store where user = %s and mall_name = %s',(token_data.get('user'),data.mall_name))
                if sql_data:
                    print(sql_data)
                    for i in sql_data:
                        mall_name.append({'id':i[0],'mall_name':i[1],'creation_time':i[2]})
                    return {'mall_name':mall_name,'current':True}
                else:
                    return {'error':'该店铺不存在','current':False}
        else:
            return {'error':'token 验证失败','current':False}
    except Exception as e:
        return {'error':str(e),'current':False}