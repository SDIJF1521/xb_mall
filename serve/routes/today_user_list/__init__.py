from datetime import date

import aiomysql
from fastapi import APIRouter, Form, Depends, HTTPException

from services.management_token_verify import ManagementTokenVerify
from data.sql_client import get_db,execute_db_query
router = APIRouter()
@router.post('/today_user_list')
async def today_user_list(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db)):
    try:
        verify = ManagementTokenVerify(token=token)
        data = await execute_db_query(db,'select user from manage_user')
        if await verify.run(data=data)['current']:
            query = 'SELECT * FROM user WHERE time = %s'
            params = (date.today(),)
            result = await execute_db_query(db,query,params)
            return {'user_list':[i[0] for i in result],'current':True}
        else:
            return {'msg':'token验证失败','current':False} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))