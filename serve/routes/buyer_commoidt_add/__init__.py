import os
from datetime import date
from typing import Annotated,List
from pydantic import Field

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Form,File,UploadFile

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.data_mods import CommodityAdd
from data.sql_client import execute_db_query,get_db
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()
@router.post("/buyer_commodity_add")
async def commodity_add(data:Annotated[CommodityAdd,Form(),File()],
                        db:Connection=Depends(get_db),
                        redis:RedisClient=Depends(get_redis),
                        mongodb:MongoDBClient=Depends(get_mongodb_client)):
    
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    async def execute():
        sql_data = await execute_db_query(db,'select MAX(shopping_id) from shopping where mall_id = %s',(data.stroe_id))
        img = []
        print(sql_data)
        if not sql_data[0][0] is None:
            shopping_id = sql_data[0][0] + 1
        else:
            shopping_id = 1

        

        await execute_db_query(db,
                               'insert into shopping(mall_id,shopping_id,stock,money,classify_categorize,time) values(%s,%s,%s,%s,%s,%s)',
                               (data.stroe_id,shopping_id,data.stock,data.price,data.classify_categorize,date.today().strftime("%Y-%m-%d")))
        
        path = f'./shopping_img/{data.stroe_id}_{shopping_id}'
        if not os.path.exists(path):
            os.makedirs(path)
        
        for idx, file in enumerate(data.img_list):
            with open(f'{path}/{idx}.jpg', 'wb') as f:
                f.write(file.file.read())
                img.append(f'{path}/{idx}.jpg')

        mongodb_data = {"mall_id":data.stroe_id,
                        "shopping_id":shopping_id,
                        "name":data.name,
                        "type":data.type,
                        "price":data.price,
                        "classify_categorize":data.classify_categorize,
                        "stock":data.stock,
                        "info":data.info,
                        "img_list":img,
                        "time":date.today().strftime("%Y-%m-%d")
                        }
        await mongodb.insert_one('shopping',mongodb_data)

        return {"code":200,"msg":"添加成功",'current':True}


    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {"code":403,"msg":"验证失败",'current':False}
        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if execute_code[1] and execute_code[2] and verify_data:
                return await execute()
            else:
                return {"code":403,"msg":"您没有权限执行此操作",'current':False}
    except Exception as e:
        return {"code":500,"msg":str(e),'current':False}
