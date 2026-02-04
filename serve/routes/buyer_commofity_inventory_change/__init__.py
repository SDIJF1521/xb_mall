from typing import Annotated

from datetime import datetime,date
from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerCommodityRepertoryChange
from data.sql_client_pool import get_db_pool,db_pool
from data.redis_client import get_redis,RedisClient
from data.mongodb_client import get_mongodb_client,MongoDBClient

router = APIRouter()

@router.patch("/buyer_commofity_inventory_change")
async def change_commodity_repertory(
                                    data:Annotated[BuyerCommodityRepertoryChange,Form(...)],
                                    db:Connection = Depends(get_db_pool),
                                    redis:RedisClient = Depends(get_redis),
                                    mongo:MongoDBClient = Depends(get_mongodb_client)
                                    ):
    
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    sql = db_pool

    if token_data is None:
        return {"code":403,"msg":"无效的token",'current':False}
    
    async def execute():
        cache = CacheService(redis)
        select_data = await sql.execute_query(
                                            'select * from specification where mall_id = %s and (shopping_id = %s and specification_id =  %s)',
                                            (data.stroe_id,data.shopping_id,data.sku_id))
        
        # 库存变更记录函数
        async def info():
            msg = {'user':token_data.get('user'),
                       'mall_id':data.stroe_id,
                       'shopping_id':data.shopping_id,
                       'specification_id':data.sku_id,
                       'change_type': "设置" if data.change_type is None else "增加" if data.change_type == 1 else "减少",
                       'change_num':data.change_num,
                       'maximum_inventory':data.maximum_inventory,
                       'minimum_balance':data.minimum_balance,
                       "time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       'info':None
                       }
            if data.info is not None:
                msg['info'] = data.info
            await mongo.insert_one('inventory_records',msg)
            await cache.delete_pattern(f'commodity:repertory:list:{data.stroe_id}:*')
            await cache.delete_pattern(f'commodity:list:{data.stroe_id}:*')
            await cache.delete_pattern(f'commodity:repertory:records:{data.stroe_id}:{data.shopping_id}:{data.sku_id}:*')

        if data.maximum_inventory < data.minimum_balance:
            return {"code":400,"msg":"最大库存不能小于最小库存",'current':False}
        
        if data.minimum_balance <=0: 
            return {"code":400,"msg":"最小库存不能小于0",'current':False}
        
        if select_data:
            if data.change_type is None:
                print(f'最小库存{data.minimum_balance}\n最大库存{data.maximum_inventory}\n变更数量{data.change_num}')
                if data.change_num > data.maximum_inventory or data.change_num < data.minimum_balance:
                    return {"code":400,"msg":"库存数量超出范围",'current':False}
                
                await sql.execute_query(
                                            'update specification set stock = %s, ' \
                                                                  'maximum_inventory = %s, ' \
                                                                  'minimum_balance = %s ' \
                                                                  'time = %s'\
                                            'where mall_id = %s '
                                            'and (shopping_id = %s and specification_id = %s)',
                                            (data.change_num,
                                             data.maximum_inventory,
                                             data.minimum_balance,
                                             datetime.now().strftime("%Y-%m-%d"),
                                             data.stroe_id,
                                             data.shopping_id,
                                             data.sku_id)
                                        )
                await mongo.update_one('shopping',
                                       {'mall_id':data.stroe_id,'shopping_id':data.shopping_id,'specification_list.specification_id':data.sku_id},
                                       {'$set':{
                                           "specification_list.$.stock":data.change_num
                                       }})

                await info()
                return {"code":200,"msg":"库存变更成功",'current':True}
            elif data.change_type:
                if data.maximum_inventory < select_data[0][4]+data.change_num:
                    return {"code":400,"msg":"增加后库存超出最大库存",'current':False}
                await sql.execute_query(
                                        'update specification set stock = stock + %s, ' \
                                                                'maximum_inventory = %s, ' \
                                                                'minimum_balance = %s,' \
                                                                 'time = %s'\
                                        'where mall_id = %s '
                                        'and (shopping_id = %s and specification_id = %s)',
                                        (data.change_num,
                                            data.maximum_inventory,
                                            data.minimum_balance,
                                            datetime.now().strftime("%Y-%m-%d"),
                                            data.stroe_id,
                                            data.shopping_id,
                                            data.sku_id)
                                    )
                await mongo.update_one('shopping',
                        {'mall_id':data.stroe_id,'shopping_id':data.shopping_id,'specification_list.specification_id':data.sku_id},
                        {'$set':{
                            "specification_list.$.stock":select_data[0][4]+data.change_num
                        }})
                await info()
                return {"code":200,"msg":"库存变更成功",'current':True}
            else:
                if data.minimum_balance > select_data[0][4]-data.change_num:
                    return {"code":400,"msg":"减少后库存低于最小库存",'current':False}
                await sql.execute_query(
                                        'update specification set stock = stock - %s, ' \
                                                                'maximum_inventory = %s, ' \
                                                                'minimum_balance = %s,' \
                                                                 'time = %s'\
                                        'where mall_id = %s '
                                        'and (shopping_id = %s and specification_id = %s)',
                                        (data.change_num,
                                            data.maximum_inventory,
                                            data.minimum_balance,
                                            datetime.now().strftime("%Y-%m-%d"),
                                            data.stroe_id,
                                            data.shopping_id,
                                            data.sku_id)
                                    )
                await mongo.update_one('shopping',
                        {'mall_id':data.stroe_id,'shopping_id':data.shopping_id,'specification_list.specification_id':data.sku_id},
                        {'$set':{
                            "specification_list.$.stock":select_data[0][4]-data.change_num
                        }})
                await info()
                return {"code":200,"msg":"库存变更成功",'current':True}
        else:
            return {"code":404,"msg":"商品不存在",'current':False}


    if token_data.get('station') == '1':
        sql_data = await sql.execute_query('select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data[0]:
            if data.stroe_id not in token_data.get('state_id_list'):
                return {'code': 403, 'msg': '您没有权限操作该店铺的库存变更', 'current': False}
            return await execute()
        else:
            return {"code":403,"msg":"无效的token",'current':False}
        
    else:
        role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                      db=db,
                                                      redis=redis,
                                                      name=token_data.get('user'),
                                                      mall_id=token_data.get('mall_id'))
        
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await sql.execute_query(
                                        'select user from store_user where user = %s and store_id = %s',
                                        (token_data.get('user'), token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if execute_code[4] and execute_code[1] and verify_data[0]:
            if data.stroe_id != token_data.get('mall_id'):
                return {'code': 403, 'msg': '您没有权限操作该店铺的库存变更', 'current': False}
            return await execute()
        else:
            return {'code': 403, 'msg': '您没有权限执行此操作', 'current': False}