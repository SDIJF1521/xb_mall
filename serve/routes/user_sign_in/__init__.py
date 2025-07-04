import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form
from data.sql_client import get_db, execute_db_query

from services.log_in import LogIn

router = APIRouter()

@router.post('/user_sign_in')

async def user_sgin(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db)) ->dict:
    try:
        database_data = await execute_db_query(db,'select user FROM user')
        log_in = LogIn(token=token)
        return await log_in.run(database_data)
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')
