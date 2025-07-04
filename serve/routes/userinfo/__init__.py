import base64

import aiomysql
from fastapi import APIRouter, Form, HTTPException, Depends

from data.sql_client import get_db, execute_db_query
from services.user_info import UserInfo
router = APIRouter()
@router.post("/userinfo")
async def userinfo(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db)) -> dict:
    try:
        user_info = UserInfo(token)
        info = await user_info.token_analysis()
        database_data = await execute_db_query(db,'select user FROM user WhERE user = %s', info['user'])
        sql = await user_info.read(database_data)
        if sql['current']:
            data = await execute_db_query(db,sql['query'],sql['params'])
            out_data = list(data[0])
            if not out_data[4] is None:
                with open(out_data[4],'rb') as f:
                    out_data[4] = base64.b64encode(f.read()).decode('utf-8')
            return {'data':out_data,'current':True}
            
        else:
            return {'msg':sql['msg'],'current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')