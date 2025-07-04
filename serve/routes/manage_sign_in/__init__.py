from typing import Annotated

import aiomysql
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter,Depends,Form,HTTPException

from data.data_mods import ManageSignIn
from data.sql_client import get_db, execute_db_query

from services.manage_login import ManageLogin

router = APIRouter()
@router.post('/manage_sign_in')
async def manage_sign_in(data:OAuth2PasswordRequestForm=Depends(),db:aiomysql.Connection = Depends(get_db)):
    try:
        database_data =  await execute_db_query(db,'select user,password FROM manage_user WhERE user = %s',data.username)
        manage_login = ManageLogin(data.username,data.password)

        return await manage_login.check_password(database_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")