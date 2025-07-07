import aiomysql
from fastapi import APIRouter,HTTPException,Depends,Form

from data.sql_client import get_db,execute_db_query
from services.management_token_verify import ManagementTokenVerify

def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()
@router.post('/user_list')
async def user_list(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    try:
        Verify = ManagementTokenVerify(token=token,redis_client=redis_client)

        data = await execute_db_query(db,'select user from manage_user')
        Verify_data = await Verify.run(data=data)
        if Verify_data['current']:
            query = 'SELECT user FROM user'
            result = await execute_db_query(db,query)
            user_list = [i[0] for i in result]
            return {'user_list':user_list,"current":True}
        else:
            return {'msg':'token验证失败',"current":False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))