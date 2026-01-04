import os
import json
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
    """
    商户添加商品接口
    流程：Token验证 -> 权限检查 -> 生成商品ID -> 保存图片 -> 插入MySQL和MongoDB
    权限：主商户(station=1)直接通过，店铺用户需要写入权限(execute_code[1])和查询权限(execute_code[2])
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()

    if token_data is None:
        return {"code":403,"msg":"无效的token",'current':False}

    async def execute():
        """执行商品添加的核心逻辑"""
        # 生成商品ID（自增）
        sql_data = await execute_db_query(db,'select MAX(shopping_id) from shopping where mall_id = %s',(data.stroe_id))
        specification_sql = await execute_db_query(db,'select MAX(specification_id) from specification where mall_id = %s',(data.stroe_id))
        img = []
        
        if not sql_data[0][0] is None:
            shopping_id = sql_data[0][0] + 1
        else:
            shopping_id = 1

        # 插入商品基础信息到MySQL（mall_id, shopping_id, 分类, 时间）
        await execute_db_query(db,
                               'insert into shopping(mall_id,shopping_id,classify_categorize,time) values(%s,%s,%s,%s)',
                               (data.stroe_id,shopping_id,data.classify_categorize,date.today().strftime("%Y-%m-%d")))
        
        # 生成规格ID
        if not specification_sql[0][0] is None:
            specification_id = int(specification_sql[0][0])
        else:
            specification_id = 0

        # 解析SKU列表并插入规格信息
        sku_list = json.loads(data.sku_list) if data.sku_list else []
        for i in sku_list:
           specification_id+=1
           await execute_db_query(db,
                                'insert into specification(mall_id,shopping_id,specification_id,price,stock) values (%s,%s,%s,%s,%s)',
                                (data.stroe_id,shopping_id,specification_id,i.get('price'),i.get('stock'))
           )
           i.update({'specification_id':specification_id})
        
        # 保存商品图片到本地
        path = f'./shopping_img/{data.stroe_id}_{shopping_id}'
        if not os.path.exists(path):
            os.makedirs(path)
        
        for idx, file in enumerate(data.img_list):
            with open(f'{path}/{idx}.jpg', 'wb') as f:
                f.write(file.file.read())
                img.append(f'{path}/{idx}.jpg')

        # 插入商品详细信息到MongoDB（包含图片路径、规格列表等）
        mongodb_data = {"mall_id":data.stroe_id,
                        "shopping_id":shopping_id,
                        "name":data.name,
                        "type":data.type,
                        "info":data.info,
                        "img_list":img,
                        "specification_list":sku_list,
                        "time":date.today().strftime("%Y-%m-%d"),
                        "audit":0  # 0表示待审核
                        }
        await mongodb.insert_one('shopping',mongodb_data)

        return {"code":200,"msg":"添加成功",'current':True}

    try:
        # 主商户：直接通过，无需权限检查
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {"code":403,"msg":"验证失败",'current':False}
        # 店铺用户：需要检查商品管理权限
        else:
            role_authority_service = RoleAuthorityService(token_data.get('role'),db)
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            # 解析权限码，execute_code[1]和[2]分别对应写入和查询权限
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            # 检查权限：execute_code[1]=写入权限，execute_code[2]=查询权限
            if execute_code[1] and execute_code[2] and verify_data:
                return await execute()
            else:
                return {"code":403,"msg":"您没有权限执行此操作",'current':False}
    except Exception as e:
        return {"code":500,"msg":str(e),'current':False}