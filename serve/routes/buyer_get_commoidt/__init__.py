import base64
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Query,Header,HTTPException


from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.data_mods import CommodityList
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.get("/buyer_get_commoidt")
async def buyer_get_commoidt(
                            data:Annotated[CommodityList,Query(...)],
                            access_token:str = Header(...),
                            db:Connection=Depends(get_db),
                            redis:RedisClient=Depends(get_redis),
                            mongodb:MongoDBClient=Depends(get_mongodb_client)):
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()
    offset = (data.page - 1) * 20
    async def execute():
        mongodb_commoidt_info = await mongodb.find_many('shopping',{'mall_id':data.stroe_id},limit=20,skip=offset)

        n = await execute_db_query(db,'select count(*) from shopping where mall_id = %s',(data.stroe_id))
        
        sql_commoidt_info = await execute_db_query(db,
                                                   'select * from shopping where mall_id = %s LIMIT %s,%s',
                                                   (data.stroe_id,offset,20))
        if mongodb_commoidt_info and sql_commoidt_info:
            mongodb_sql_dic = {i['shopping_id']:{
                                                    'name':i['name'],
                                                    'types':i['type'],
                                                    'info':i['info'],
                                                    'img_list':i['img_list'],
                                                    'specification_list':i['specification_list']
                                                 } for i in mongodb_commoidt_info}
            out = []
            for i in sql_commoidt_info:
                print(mongodb_sql_dic)
                img_list = []
                for j in mongodb_sql_dic[i[1]]['img_list']:
                    with open(j,'rb') as f:
                        img_list.append(base64.b64encode(f.read()).decode('utf-8'))
                content = {
                    'id':i[1],
                    'name':mongodb_sql_dic[i[1]]['name'],
                    'classify_categorize':i[4],
                    'types':mongodb_sql_dic[i[1]]['types'],
                    'info':mongodb_sql_dic[i[1]]['info'],
                    'img_list':img_list,
                    'specification_list':mongodb_sql_dic[i[1]]['specification_list'],
                    'audit':i[4],
                    'time':i[3]

                }
                out.append(content)

            return {'code':200,'msg':'获取成功','success':True,'data':out,'page':n[0][0]}
        else:
            return {'code':404,'msg':'获取失败','success':False}



    if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {'code':403,'msg':'验证失败','success':False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code[1] and verify_data:
            return await execute()
        else:
             return {'code':403,'msg':'权限不足','success':False}