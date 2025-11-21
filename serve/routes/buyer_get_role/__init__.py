from typing import Annotated

from fastapi import APIRouter,HTTPException,Depends,Form

from services.verify_duter_token import VerifyDuterToken

from data.data_mods import BuyerGetRole
from data.sql_client import get_db,execute_db_query
from data.redis_client import get_redis,RedisClient

router = APIRouter()
@router.post('/buyer_get_role')
async def change_user_role(
    data:Annotated[BuyerGetRole,Form()],
    db: get_db = Depends(get_db),
    redis: get_redis = Depends(get_redis)
):
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute(id):
        query = """
        SELECT * FROM store_role WHERE mall_id = %s OR mall_id is Null
        """
        result = await execute_db_query(db, query, (id))
        print(result)
        data = {}
        if result:
            data = [{i[0]:[i[1],i[3]]} for i in result]
            return {'code':200,'msg':'操作成功','data':data,'current':True}
        else:
            return {'code':400,'msg':'操作失败','data':data,'current':False}
    
    if token_data.get('station') == '1':
        return await execute(data.stroe_id)
    else:
        if token_data.get('role') == 1:
            return await execute(data.stroe_id)
        else:
            return {'code':400,'msg':'权限不足','data':data,'current':False}
        
