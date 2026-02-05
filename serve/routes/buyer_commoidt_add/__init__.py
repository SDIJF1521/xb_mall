import os
import json
from datetime import date
from typing import Annotated,List
from pydantic import Field

from aiomysql import Connection
from fastapi import APIRouter,Depends,HTTPException,Form,File,UploadFile

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

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
    """商户添加商品"""
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    if token_data is None:
        return {"code":403,"msg":"无效的token",'current':False}

    async def execute():
        classify_check = await execute_db_query(
            db,
            'select id from classify where id = %s and (store_id is Null or store_id = %s)',
            (data.classify_categorize, data.stroe_id)
        )
        
        if not classify_check or len(classify_check) == 0:
            return {
                "code": 400,
                "msg": f"分类ID {data.classify_categorize} 不存在或不属于当前店铺，请选择有效的商品分类",
                'current': False
            }
        
        sql_data = await execute_db_query(db,'select MAX(shopping_id) from shopping where mall_id = %s',(data.stroe_id))
        specification_sql = await execute_db_query(db,'select MAX(specification_id) from specification where mall_id = %s',(data.stroe_id))
        img = []
        
        if not sql_data[0][0] is None:
            shopping_id = sql_data[0][0] + 1
        else:
            shopping_id = 1

        await execute_db_query(db,
                               'insert into shopping(mall_id,shopping_id,classify_categorize,time) values(%s,%s,%s,%s)',
                               (data.stroe_id,shopping_id,data.classify_categorize,date.today().strftime("%Y-%m-%d")))
        
        if not specification_sql[0][0] is None:
            specification_id = int(specification_sql[0][0])
        else:
            specification_id = 0

        sku_list = json.loads(data.sku_list) if data.sku_list else []
        for i in sku_list:
           specification_id+=1
           await execute_db_query(db,
                                'insert into specification(mall_id,shopping_id,specification_id,price,stock,time) values (%s,%s,%s,%s,%s,%s)',
                                (data.stroe_id,shopping_id,specification_id,i.get('price'),i.get('stock'),date.today().strftime("%Y-%m-%d"))
           )
           i.update({'specification_id':specification_id})
        
        path = f'./shopping_img/{data.stroe_id}_{shopping_id}'
        if not os.path.exists(path):
            os.makedirs(path)
        
        for idx, file in enumerate(data.img_list):
            with open(f'{path}/{idx}.jpg', 'wb') as f:
                f.write(file.file.read())
                img.append(f'{path}/{idx}.jpg')

        if data.type is None:
            type_list = []
        elif isinstance(data.type, str):
            type_list = [tag.strip() for tag in data.type.split(',') if tag.strip()]
        elif isinstance(data.type, list):
            type_list = data.type
        else:
            type_list = []
        
        mongodb_data = {"mall_id":data.stroe_id,
                        "shopping_id":shopping_id,
                        "name":data.name,
                        "type":type_list,
                        "info":data.info,
                        "img_list":img,
                        "specification_list":sku_list,
                        "time":date.today().strftime("%Y-%m-%d"),
                        "audit":0
                        }
        await mongodb.insert_one('shopping',mongodb_data)
        
        cache = CacheService(redis)
        await cache.delete_pattern(f'commodity:list:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:search:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:repertory:list:{data.stroe_id}')
        await cache.delete_pattern(f'commodity:repertory:search:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:repertory:all:{data.stroe_id}')

        return {"code":200,"msg":"添加成功",'current':True}

    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data[0]:
                if data.stroe_id not in token_data.get('state_id_list'):
                    return {'code': 403, 'msg': '您没有权限操作该店铺的商品', 'current': False}
                return await execute()
            else:
                return {"code":403,"msg":"验证失败",'current':False}
        else:
            role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                          db=db,
                                                          redis=redis,
                                                          name=token_data.get('user'),
                                                          mall_id=token_data.get('mall_id'))
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if execute_code[1] and execute_code[2] and verify_data[0]:
                if data.stroe_id != token_data.get('mall_id'):
                    return {'code': 403, 'msg': '您没有权限操作该店铺的商品', 'current': False}
                return await execute()
            else:
                return {"code":403,"msg":"您没有权限执行此操作",'current':False}
    except Exception as e:
        return {"code":500,"msg":str(e),'current':False}