
import aiomysql
from fastapi import APIRouter,Depends

from services.on_line import OnLine
from services.management_token_verify import ManagementTokenVerify
from data.sql_client import execute_db_query,get_db
def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()
@router.get('/get_online_user_list')
async def get_online_user_list(token,redis_client=Depends(get_redis),db:aiomysql.Connection = Depends(get_db)):
    Verify = ManagementTokenVerify(token=token,redis_client=redis_client)

    sql_data = await execute_db_query(db,'select user from manage_user')
    Verify_data = await Verify.run(sql_data)
    online = OnLine(redis_client=redis_client)
    if Verify_data['current']:
        data = await online.get_online_users()
        return data
    else:
        return {'msg':'验证失败','current':False}