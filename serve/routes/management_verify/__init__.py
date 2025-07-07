import aiomysql
from fastapi import APIRouter,HTTPException,Depends,Form

from services.management_token_verify import ManagementTokenVerify

from data.sql_client import execute_db_query,get_db

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()
@router.post('/management_verify')
async def management_verify(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    try:
        management_token_verify = ManagementTokenVerify(token=token,redis_client=redis_client)
        data = await execute_db_query(db,'select user from manage_user')
        return await management_token_verify.run(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
