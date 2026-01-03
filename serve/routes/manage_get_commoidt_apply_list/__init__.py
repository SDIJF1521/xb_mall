import base64
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Query,Header,HTTPException

from services.management_token_verify import ManagementTokenVerify

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client
from data.data_mods import ManageGetCommodityApplyList

# 管理员获取商品上架申请列表路由
router = APIRouter()
@router.get('/manage_get_commoidt_apply_list')
async def manage_get_commoidt_apply(data:Annotated[ManageGetCommodityApplyList,Query(...)],
                                    access_token:str = Header(...),
                                    db:Connection=Depends(get_db),
                                    redis:RedisClient=Depends(get_redis),
                                    mongodb:MongoDBClient=Depends(get_mongodb_client)):

    verify = ManagementTokenVerify(token=access_token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()

    async def execute():
        if data.select_data is None:
            offset = (data.page - 1) * 20
            mongodb_data = await mongodb.find_many('shopping',{'audit':0},limit=data.page,skip=offset)
            n = await execute_db_query(db,'select count(*) from shopping where audit = 0')
            if mongodb_data:
                out = []
                for i in mongodb_data:
                    out.append({
                        'mall_id':i['mall_id'],
                        'shopping_id':i['shopping_id'],
                        'name':i['name'],
                        'types':i['type'],
                        'info':i['info'],
                        'time':i['time']
                    })
                return {'current':True,'commodity_list':out,'page':n[0][0]}

            else:
                return {'current':False,'msg':'暂无数据'}
        else:
            offset = (data.page - 1) * 20
            
            mongodb_data = await mongodb.find_many('shopping',{'name':data.select_data,'audit':0},limit=data.page,skip=offset)
            out = []
            if mongodb_data:
                for i in mongodb_data:
                    out.append({
                        'mall_id':i['mall_id'],
                        'shopping_id':i['shopping_id'],
                        'name':i['name'],
                        'types':i['type'],
                        'info':i['info'],
                        'time':i['time']
                    })
                return {'current':True,'commodity_list':out,'page':len(mongodb_data)}
            else:
                return {'current':False,'msg':'暂无数据'}

    try:
        sql_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
        Verify_data = await verify.run(sql_data)
        if Verify_data['current']:
            return await execute()
        else:
            return {'current':False,'msg':'验证失败','code':401}    
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))