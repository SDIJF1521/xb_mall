from aiomysql import Connection
from fastapi import APIRouter,Depends,Query,Header,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis

# 获取分类
router = APIRouter()

@router.get('/buter_get_classify')
async def get_classify(
    store_id:int = Query(...,description='店铺id'),
    access_token: str = Header(..., description="Duter token"),
    db: Connection = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute():
        sql = 'select id,name from classify where store_id is Null or store_id = %s'
        sql_data = await execute_db_query(db,sql,(store_id,))
        out_data = {i[0]:i[1] for i in sql_data}
        return {'code':200,'msg':'获取成功','current':True,'data':out_data}

    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            return {'code':403,'msg':'验证失败','current':False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code[2] and verify_data:
            return await execute()
        else:
            return {'code':403,'msg':'您没有权限执行此操作','current':False}