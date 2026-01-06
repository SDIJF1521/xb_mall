import aiomysql
from fastapi import APIRouter,HTTPException,Depends,Form

from services.management_token_verify import ManagementTokenVerify

from data.sql_client import execute_db_query,get_db

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()

@router.post('/management_verify')
async def management_verify(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    """
    管理员Token验证
    """
    try:
        management_token_verify = ManagementTokenVerify(token=token,redis_client=redis_client)
        admin_tokrn_content = await management_token_verify.token_admin()
        if admin_tokrn_content['current']:
            admin = admin_tokrn_content['user']
            data = await execute_db_query(db,f'select * from manage_user where user = "{admin}"')
            return await management_token_verify.run(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
