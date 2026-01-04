import base64

import aiomysql
from fastapi import APIRouter, Form, HTTPException, Depends

from data.sql_client import get_db, execute_db_query
from services.user_info import UserInfo
router = APIRouter()

@router.post("/userinfo")
async def userinfo(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db)) -> dict:
    """
    获取用户详细信息接口
    流程：Token验证 -> 查询用户信息 -> 头像转Base64编码
    返回：用户基本信息（包含头像Base64编码）
    """
    try:
        user_info = UserInfo(token)
        # 解析Token获取用户信息
        info = await user_info.token_analysis()
        database_data = await execute_db_query(db,'select user FROM user WhERE user = %s', info['user'])
        sql = await user_info.read(database_data)
        if sql['current']:
            # 查询用户详细信息
            data = await execute_db_query(db,sql['query'],sql['params'])
            out_data = list(data[0])
            # 将用户头像转为Base64编码
            if not out_data[4] is None:
                with open(out_data[4],'rb') as f:
                    out_data[4] = base64.b64encode(f.read()).decode('utf-8')
            return {'data':out_data,'current':True}
            
        else:
            return {'msg':sql['msg'],'current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail='服务器内部错误')