from typing import Annotated

import aiomysql

from data.data_mods import UserRegister
from data.sql_client import get_db, execute_db_query
from fastapi import APIRouter, Depends, HTTPException,Form
from services.register import Register

router = APIRouter()

@router.post('/register')
async def register(data:Annotated[UserRegister,Form()], db:aiomysql.Connection = Depends(get_db)) -> dict:
    try:
        print(data.captcha)
        user_list = await execute_db_query(db,'select user FROM user')
        email_list = await execute_db_query(db,'select email FROM user')
        A = Register(email=data.email, user=data.user_name, password=data.user_password,code=data.captcha)
        value = await A.user_add(user_list,email_list)
        print(value)
        if isinstance(value,str):
            return {'msg':value,'current':False}
        elif isinstance(value,list):
            raise HTTPException(status_code=500, detail=f"{value}")
        else:
            for i in value:
                await execute_db_query(db,value[i]['query'],value[i]['params'])
            return {'msg':'注册成功','current':True}
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")