from datetime import date

import aiomysql
from fastapi import APIRouter, Form, Depends, HTTPException

from services.management_token_verify import ManagementTokenVerify
from data.sql_client import get_db,execute_db_query

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()
@router.post('/today_user_list')
async def today_user_list(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    try:
        verify = ManagementTokenVerify(token=token,redis_client=redis_client)

        data = await execute_db_query(db,'select user from manage_user')
        verify_vul = await verify.run(data=data)
        print(verify_vul)
        if verify_vul['current']:
            query = 'SELECT * FROM user WHERE time = %s'
            params = (date.today(),)
            result = await execute_db_query(db,query,params)
            return {'user_list':[i[0] for i in result],'current':True}
        else:
            return {'msg':'token验证失败','current':False} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))