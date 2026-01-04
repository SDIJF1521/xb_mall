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
    """
    获取商品列表接口（支持搜索和分页）
    流程：Token验证 -> 权限检查 -> 从MongoDB查询商品详情 -> 从MySQL查询基础信息 -> 合并数据并转Base64图片
    权限：主商户直接通过，店铺用户需要查询权限(execute_code[2])
    """
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()
    offset = (data.page - 1) * 20  # 分页偏移量（每页20条）
    
    async def execute():
        """执行商品查询的核心逻辑"""
        if data.select is not None and data.select.strip():
            # 模糊搜索：使用MongoDB的正则表达式搜索商品名称
            search_pattern = data.select.strip()
            mongodb_filter = {
                'mall_id': data.stroe_id,
                'name': {'$regex': search_pattern, '$options': 'i'}  # 不区分大小写
            }
            all_mongodb_commoidt_info = await mongodb.find_many('shopping', mongodb_filter)
            
            if all_mongodb_commoidt_info:
                # 获取所有匹配的商品ID并分页
                shopping_ids = [item['shopping_id'] for item in all_mongodb_commoidt_info]
                total_count = len(shopping_ids)
                paginated_shopping_ids = shopping_ids[offset:offset + 20]
                
                if paginated_shopping_ids:
                    paginated_ids_set = set(paginated_shopping_ids)
                    mongodb_commoidt_info = [item for item in all_mongodb_commoidt_info if item['shopping_id'] in paginated_ids_set]
                    
                    # 从MySQL查询对应商品的基础信息
                    placeholders = ','.join(['%s'] * len(paginated_shopping_ids))
                    sql_commoidt_info = await execute_db_query(db,
                                                            f'select * from shopping where mall_id = %s and shopping_id in ({placeholders})',
                                                            (data.stroe_id, *paginated_shopping_ids))
                else:
                    mongodb_commoidt_info = []
                    sql_commoidt_info = []
                
                n = [[total_count]]
            else:
                mongodb_commoidt_info = []
                sql_commoidt_info = []
                n = [[0]]
        else:
            # 普通查询（无搜索条件）：直接分页查询
            mongodb_commoidt_info = await mongodb.find_many('shopping', {'mall_id': data.stroe_id}, limit=20, skip=offset)
            n = await execute_db_query(db, 'select count(*) from shopping where mall_id = %s', (data.stroe_id,))
            
            sql_commoidt_info = await execute_db_query(db,
                                                    'select * from shopping where mall_id = %s LIMIT %s,%s',
                                                    (data.stroe_id, offset, 20))
        
        # 合并MongoDB和MySQL数据，并将图片转为Base64编码
        if mongodb_commoidt_info and sql_commoidt_info:
            # 构建商品详情字典（以shopping_id为key）
            mongodb_sql_dic = {i['shopping_id']:{
                                                    'name':i['name'],
                                                    'types':i['type'],
                                                    'info':i['info'],
                                                    'img_list':i['img_list'],
                                                    'specification_list':i['specification_list']
                                                 } for i in mongodb_commoidt_info}
            out = []
            for i in sql_commoidt_info:
                img_list = []
                # 将图片文件转为Base64编码
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
        elif data.select is not None and data.select.strip():
            return {'code':200,'msg':'获取成功','success':True,'data':[],'page':0}
        else:
            return {'code':404,'msg':'获取失败','success':False}

    # 主商户：直接通过
    if token_data.get('station') == '1':
            sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data:
                return await execute()
            else:
                return {'code':403,'msg':'验证失败','success':False}
    # 店铺用户：需要查询权限
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        # execute_code[2]表示查询权限
        if execute_code[2] and verify_data:
            return await execute()
        else:
             return {'code':403,'msg':'权限不足','success':False}