
import aiomysql
from fastapi import APIRouter,Depends,HTTPException

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
    try:
        Verify = ManagementTokenVerify(token=token,redis_client=redis_client)
        admin_tokrn_content = await Verify.token_admin()
        if admin_tokrn_content['current']:

            sql_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
            Verify_data = await Verify.run(sql_data)
            online = OnLine(redis_client=redis_client)
            if Verify_data['current']:
                data = await online.get_online_users()
                return data
            else:
                return {'msg':'验证失败','current':False}
        else:
            return {'msg':'token验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
