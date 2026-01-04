from typing import Annotated

import aiomysql
from pydantic import EmailStr

from data.data_mods import UserRegister
from data.sql_client import get_db, execute_db_query
from fastapi import APIRouter, Depends, HTTPException,Form
from services.register import Register

router = APIRouter()

@router.post('/register')
async def register(
    email: EmailStr = Form(...),
    user_name: str = Form(...),
    user_password: str = Form(...),
    captcha: str = Form(...),
    db: aiomysql.Connection = Depends(get_db)
) -> dict:
    """
    用户注册接口
    流程：验证码校验 -> 用户名/邮箱唯一性检查 -> 密码强度验证 -> 插入用户数据
    """
    try:
        data = UserRegister(
            email=email,
            user_name=user_name,
            user_password=user_password,
            captcha=captcha
        )
        # 获取所有用户名和邮箱，用于唯一性验证
        user_list = await execute_db_query(db,'select user FROM user')
        email_list = await execute_db_query(db,'select email FROM user')
        A = Register(email=data.email, user=data.user_name, password=data.user_password,code=data.captcha)
        # 执行注册业务逻辑（验证码、唯一性、密码强度等）
        value = await A.user_add(user_list,email_list)
        
        if isinstance(value,str):
            # 返回错误信息（如：验证码错误、用户名已存在等）
            return {'msg':value,'current':False}
        elif isinstance(value,list):
            # 返回错误列表
            raise HTTPException(status_code=500, detail=f"{value}")
        else:
            # 注册成功，执行数据库插入操作
            for i in value:
                await execute_db_query(db,value[i]['query'],value[i]['params'])
            return {'msg':'注册成功','current':True}
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")