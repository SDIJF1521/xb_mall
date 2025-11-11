from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import UpdateMall

router = APIRouter()

@router.patch('/buyer_update_mall')
async def buyer_update_mall(data:Annotated[UpdateMall,Form()],db:Connection=Depends(get_db),redis:RedisClient=Depends(get_redis)):
     # 验证 token
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                sel_mall_id = await execute_db_query(db,'select * from store where mall_id=%s',(data.id))
                if sel_mall_id:
                    await execute_db_query(db,'update store set mall_name=%s,mall_phone=%s,mall_site=%s,mall_describe=%s,state=%s where mall_id=%s',
                                        (data.mall_name,data.mall_site,data.mall_phone,data.info,data.state,data.id))
                    return {"code":200,"msg":"success","data":None,'current':True}
                else:
                    return {"code":400,"msg":"mall_id not found","data":None,'current':False}
            else:
                return {"code":400,"msg":"token verify failed","data":None,'current':False}
        else:
            return {"code":400,"msg":"token verify failed","data":None,'current':False}
    except Exception as e:
        return {"code":400,"msg":str(e),"data":None,'current':False}