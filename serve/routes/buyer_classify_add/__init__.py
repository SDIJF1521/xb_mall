from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Form,HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerCommodityClassifyAdd
from data.sql_client_pool import get_db_pool, db_pool
from data.redis_client import get_redis,RedisClient

router = APIRouter()
@router.post("/buyer_classify_add",summary="买家添加商品分类")
async def buyer_classify_add(
                            data:Annotated[BuyerCommodityClassifyAdd,Form(...)],
                            db:Connection = Depends(get_db_pool),
                            redis:RedisClient = Depends(get_redis)):
    
    verify_duter_token = VerifyDuterToken(data.token,redis)
    token_data = await verify_duter_token.token_data()
    # 使用全局连接池实例，而不是创建新实例
    sql = db_pool

    async def execute():
        cache = CacheService(redis)
        classify_id_max = await sql.execute_query('select IFNULL(MAX(id),0) from classify where store_id = %s or store_id is Null',(data.stroe_id))
        classify_id_max = int(classify_id_max[0][0]) + 1
        await sql.execute_query('insert into classify (id,store_id,name) values (%s,%s,%s)',
                                (classify_id_max,data.stroe_id,data.name))
        await cache.delete_pattern(f'classify:{data.stroe_id}')
        return {"code":200,"msg":"新增分类成功","data":None,'current':True}

    try:
        if token_data.get('station') == '1':
            sql_data = await sql.execute_query('select user from seller_sing where user = %s',(token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            print(verify_data)
            if verify_data[0]:
                if data.stroe_id not in token_data.get('state_id_list'):
                    return {"code":400,"msg":"您没有权限添加该店铺分类","data":None,'current':False}
                return await execute()
            else:
                return {"code":400,"msg":"验证失败","data":None,'current':False}
        else:
            role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                          db=db,
                                                          redis=redis,
                                                          name=token_data.get('user'),
                                                          mall_id=token_data.get('mall_id'))
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await sql.execute_query('select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if execute_code[1] and execute_code[4] and verify_data[0]:
                if data.stroe_id != token_data.get('mall_id'):
                    return {"code":400,"msg":"您没有权限添加该店铺分类","data":None,'current':False}
                return await execute()
            else:
                return {"code":400,"msg":"权限不足","data":None,'current':False}

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"code":500,"msg":str(e),"data":None,'current':False}