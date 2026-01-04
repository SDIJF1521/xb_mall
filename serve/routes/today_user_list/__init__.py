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
    """
    获取今日注册用户列表接口
    流程：管理员Token验证 -> 查询今日注册的用户（time=今天）-> 返回用户列表
    权限：仅管理员可访问
    """
    try:
        verify = ManagementTokenVerify(token=token,redis_client=redis_client)

        data = await execute_db_query(db,'select user from manage_user')
        verify_vul = await verify.run(data=data)
        if verify_vul['current']:
            # 查询今日注册的用户（time字段等于今天）
            query = 'SELECT * FROM user WHERE time = %s'
            params = (date.today(),)
            result = await execute_db_query(db,query,params)
            return {'user_list':[i[0] for i in result],'current':True}
        else:
            return {'msg':'token验证失败','current':False} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))