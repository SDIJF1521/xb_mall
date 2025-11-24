import base64
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Form,Depends

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.data_mods import GetMallInfo


router = APIRouter()
@router.post("/buyer_get_mall_info")
async def buyer_get_mall_info(data:Annotated[GetMallInfo,Form()],db: Connection = Depends(get_db),redis: RedisClient = Depends(get_redis)):
    # 验证 token
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()


    async def execute(mall_id:int=None):
        if data.id is None and mall_id is None:
            sql_mall_info = await execute_db_query(db,"select * from store where user = %s",(token_data.get("user")))
        elif data.id is not None:
            sql_mall_info = await execute_db_query(db,"select * from store where mall_id = %s",(data.id))
        else:
             sql_mall_info = await execute_db_query(db,"select * from store where mall_id = %s",(mall_id))
        # 返回字段处理表达式
        rtn = []
        if sql_mall_info:
            # 假设数据库结构为：id, user, mall_name, phone, site, info, img_path, time
            # 注意：第6个字段(i[6])应该是img_path而不是img
            rtn = [{"id":i[0],"user":i[1],"mall_name":i[2],"phone":i[3],"site":i[4],"info":i[5],"img":i[6],"time":i[7],'state':i[8]}for i in sql_mall_info]
            for i in rtn:
                with open(i['img'], 'rb') as f:
                    i['img'] = base64.b64encode(f.read()).decode('utf-8')
        return {"code":200,"msg":"success","data":rtn,'current':True}

    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute()
        else:
            
            return {"code":400,"msg":"token verify failed","data":None,'current':False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        if execute_code[2]:
                return await execute(token_data.get('mall_id'))
        else:
            return {"code":400,"msg":"token verify failed","data":None,'current':False}