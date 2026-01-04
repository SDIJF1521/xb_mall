from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Depends
import aiomysql

from data.data_mods import Password_reset
from data.sql_client import get_db, execute_db_query
from services.password_replacement import PasswordReplacement

router = APIRouter()

@router.patch("/password_reset")
async def password_reset(data:Annotated[Password_reset,Form()], db:aiomysql.Connection = Depends(get_db)):
    """
    密码重置接口
    流程：验证Token（来自验证码验证）-> 验证邮箱是否存在 -> 更新密码
    安全：需要先通过验证码验证获取临时Token
    """
    try:
        Replacement = PasswordReplacement(email=data.email, password=data.user_password, token=data.captcha)
        # 获取所有邮箱列表，用于验证邮箱是否存在
        sql_email_list = await execute_db_query(db,'Select email FROM user')
        email_list = [i[0] for i in sql_email_list]
        # 执行密码重置逻辑（验证Token和邮箱）
        sql = await Replacement.replacement(email_list=email_list)
        if isinstance(sql,dict):
            # 密码重置成功，执行数据库更新
            await execute_db_query(db,sql['query'],sql['params'])
            return {'msg':'密码修改成功','current':True}
        else:
            return {'msg':f'{sql}','current':False}
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")