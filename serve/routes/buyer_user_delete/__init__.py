import os
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Form

from services.verify_duter_token import VerifyDuterToken

from data.data_mods import DeleteMallUser
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

router = APIRouter()

@router.delete('/buyer_user_delete')
async def buyer_user_delete(data:Annotated[DeleteMallUser,Form()],
                            db:Connection=Depends(get_db),
                            redis:RedisClient=Depends(get_redis)):
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            print(data.user_name)
            for i in data.user_name:
                await execute_db_query(db,'delete from store_user where store_id = %s and user=%s',(data.strore_id,i))
                img = await execute_db_query(db,'select img from store_user where store_id = %s and user=%s',(data.strore_id,i))
                if img:
                    os.remove(img[0][0])
            return {'code':200,'msg':'删除成功','current':True}
        else:
             return {'code':400,'msg':'token验证失败','current':False}
        
    try:
        if token_data.get('authority') != 1:
            if token_data.get('station') == '1':
                return await execute()
            else:
                if token_data.get('role') == 1:
                    return await execute()
                else:
                    return {'code':400,'msg':'权限不足','current':False}
    except HTTPException as e:
        return {'code':400,'msg':e.detail,'current':False}
    except:
        return {'code':500,'msg':'无效参数','current':False}
            
