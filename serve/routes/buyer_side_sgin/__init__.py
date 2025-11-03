from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException

from services.verify_duter_token import VerifyDuterToken

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient



def get_redis():
    # 从 main.py 引入 verifier 实例
    from main import redis_client
    return redis_client

router = APIRouter()
@router.post('/buyer_side_verify')
async def VerifyToken(token:str,db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):
    try:
        token_verify = VerifyDuterToken(token,redis)
        token_data = await token_verify.token_data()

        if not token_data is None:
            if token_data.get('station') == '1':
                sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
                verify_data = await token_verify.verify_token(sql_data)
                print(verify_data[0])
                if verify_data[0]:

                    return {'msg':'验证通过','current':True,'station':'admin'}
                else:
                    return {'msg':'token错误或已过期','current':False}

            elif token_data.get('station') == '2':
                sql_data = await execute_db_query(db,'select user from store_user where user = %s',(token_data.get('user')))
                if verify_data[0]:
                    return {'msg':'验证通过','current':True,'station':'user'}
                else:
                    return {'msg':'token错误或已过期','current':False}


        else:
            return HTTPException(status_code=401,detail='token错误或已过期')
    except Exception as e:
        return HTTPException(status_code=500,detail=str(e))
    
