import os
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form

from services.verify_duter_token import VerifyDuterToken

from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db,execute_db_query
from data.data_mods import DeleteMall

router = APIRouter()


@router.delete('/buyer_delete_mall')
async def buyer_delete_mall(data: Annotated[DeleteMall, Form()], db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):
    # token 验证
    try:
        verifier = VerifyDuterToken(data.token,redis)
        token_data = await verifier.token_data()
        if token_data.get('station') == '1':
            sql_data_store_id = await execute_db_query(db,"select mall_id from store where mall_id = %s",(data.mall_id))
            print(sql_data_store_id)
            if not sql_data_store_id:
                return {'msg':'该店铺不存在或无权限删除','current':False}
            
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            img_path = await execute_db_query(db,"select img_path from store where mall_id = %s",(data.mall_id))
            if sql_data:
                await execute_db_query(db,'delete from store where mall_id = %s',(data.mall_id))
                if img_path:
                    os.remove(img_path[0][0])
                return {'msg':'删除成功','current':True}
            else:
                return {'msg':'删除失败','current':False}
        else:
            return {'msg':'token 验证失败','current':False}
    except Exception as e:
        return {'error':str(e),'current':False}