import os
import json
import shutil
import aiofiles
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,File,UploadFile

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import SellerCommodityEdit
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.patch('/buyer_commodity_edit')
async def buyer_commodity_edit(data:Annotated[SellerCommodityEdit,Form(),File()],
                               db:Connection=Depends(get_db),
                               redis:RedisClient=Depends(get_redis),
                               mongodb:MongoDBClient=Depends(get_mongodb_client)):
    """
    卖家端商品编辑
    """
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    
    if token_data is None:
        return {"code":403,"msg":"无效的token",'current':False}
    
    async def execute():
        sql_data = await execute_db_query(db,'select * from shopping where mall_id = %s and shopping_id = %s',(data.stroe_id,data.shopping_id))
        if not sql_data:
            return {"code":404,"msg":"商品不存在",'current':False}
        
        old_mongodb_data = await mongodb.find_one('shopping', {
            'mall_id': data.stroe_id,
            'shopping_id': data.shopping_id
        })
        
        if not old_mongodb_data:
            return {"code":404,"msg":"商品详细信息不存在",'current':False}
        
        await execute_db_query(db,
                              'update shopping set classify_categorize = %s ,audit = 0 where mall_id = %s and shopping_id = %s',
                              (data.classify_categorize, data.stroe_id, data.shopping_id))
        
        await execute_db_query(db,
                              'delete from specification where mall_id = %s and shopping_id = %s',
                              (data.stroe_id, data.shopping_id))
        
        specification_sql = await execute_db_query(db,'select MAX(specification_id) from specification where mall_id = %s',(data.stroe_id))
        if not specification_sql[0][0] is None:
            specification_id = int(specification_sql[0][0])
        else:
            specification_id = 0
        
        sku_list = json.loads(data.sku_list) if data.sku_list else []
        for i in sku_list:
            specification_id += 1
            await execute_db_query(db,
                                  'insert into specification(mall_id,shopping_id,specification_id,price,stock) values (%s,%s,%s,%s,%s)',
                                  (data.stroe_id, data.shopping_id, specification_id, i.get('price'), i.get('stock')))
            i.update({'specification_id': specification_id})
        
        img_list = []
        old_img_path = f'./shopping_img/{data.stroe_id}_{data.shopping_id}'
        new_img_path = old_img_path
        
        if data.img_list and len(data.img_list) > 0:
            valid_files = []
            for file in data.img_list:
                if file and file.filename and file.filename.strip():
                    content = await file.read()
                    if content and len(content) > 0:
                        valid_files.append((file, content))
                    await file.seek(0)
            
            if valid_files:
                if os.path.exists(old_img_path):
                    shutil.rmtree(old_img_path)
                
                if not os.path.exists(new_img_path):
                    os.makedirs(new_img_path)
                
                for idx, (file, content) in enumerate(valid_files):
                    file_path = f'{new_img_path}/{idx}.jpg'
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(content)
                    img_list.append(file_path)
            else:
                img_list = old_mongodb_data.get('img_list', [])
        else:
            img_list = old_mongodb_data.get('img_list', [])
        
        if data.type is None:
            type_list = []
        elif isinstance(data.type, str):
            type_list = [tag.strip() for tag in data.type.split(',') if tag.strip()]
        elif isinstance(data.type, list):
            type_list = data.type
        else:
            type_list = []
        
        mongodb_update_data = {
            "name": data.name,
            "type": type_list,
            "info": data.info,
            "img_list": img_list,
            "specification_list": sku_list,
            "audit": 0
        }
        
        await mongodb.update_one(
            'shopping',
            {'mall_id': data.stroe_id, 'shopping_id': data.shopping_id},
            {'$set': mongodb_update_data}
        )
        
        cache = CacheService(redis)
        await cache.delete_pattern(f'commodity:list:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:search:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:inform:*')
        await cache.delete_pattern(f'admin:commodity:detail:{data.stroe_id}:{data.shopping_id}')
        await cache.delete_pattern(f'admin:commodity:apply:*')
        await cache.delete_pattern(f'commodity:repertory:list:{data.stroe_id}:*')
        await cache.delete_pattern(f'commodity:repertory:search:{data.stroe_id}:*')
        
        old_img_list = old_mongodb_data.get('img_list', [])
        for old_img in old_img_list:
            if old_img:
                cache_key = cache._make_key('img_base64', old_img)
                await cache.delete(cache_key)
        
        for new_img in img_list:
            if new_img:
                cache_key = cache._make_key('img_base64', new_img)
                await cache.delete(cache_key)
        
        return {"code":200,"msg":"编辑成功",'current':True}

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