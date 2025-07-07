import aiomysql
from fastapi import APIRouter,Depends,Form, HTTPException

from data.sql_client import get_db,execute_db_query
from services.management_token_verify import ManagementTokenVerify

def get_redis():
    from main import redis_client
    return redis_client

router = APIRouter()
@router.post('/number_merchants')
async def NumberMerchants(token:str=Form(min_length=6),db:aiomysql.Connection = Depends(get_db),redis_client=Depends(get_redis)):
    try:
        verify = ManagementTokenVerify(token=token,redis_client=redis_client)

        data = await execute_db_query(db,'select user from manage_user')
        verify_data = await verify.run(data)
        if verify_data['current']:
            merchant = await execute_db_query(db,'select user from user where merchant = 1')
            if not merchant:
                return {'merchant_list':[],'current':True}
            else:
                merchant_list = [i[0] for i in merchant]
                return {'merchant_list':merchant_list,'current':True}
        else:
            return {'msg':'不是管理员用户','current':False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))