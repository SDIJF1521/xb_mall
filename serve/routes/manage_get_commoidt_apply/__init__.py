import base64
from typing import Annotated

from aiomysql import Connection
from fastapi import APIRouter,Depends,Query,Header,HTTPException

from services.management_token_verify import ManagementTokenVerify

from data.data_mods import ManageGetCommodityApplyDetail
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoClient,get_mongodb_client

# 管理员获取商品上架申请详情路由
router = APIRouter()

@router.get('/manage_get_commoidt_apply_detail')
async def manage_get_commoidt_apply_detail(data:Annotated[ManageGetCommodityApplyDetail,Query(...)],
                                            access_token:str = Header(...),
                                            db:Connection=Depends(get_db),
                                            redis:RedisClient=Depends(get_redis),
                                            mongodb:MongoClient=Depends(get_mongodb_client)):
    try:
        verify = ManagementTokenVerify(token=access_token,redis_client=redis)
        admin_tokrn_content = await verify.token_admin()
        
        async def execute():
            sql_commoidt_data = await execute_db_query(db,
                                                       'select * from shopping where mall_id= %s and shopping_id = %s and audit = 0',
                                                       (data.mall_id,data.shopping_id))
            mongodb_specification_data = await mongodb.find_one('shopping',{'mall_id':data.mall_id,'shopping_id':data.shopping_id,'audit':0})   
            if sql_commoidt_data and mongodb_specification_data:
                classify = await execute_db_query(db,
                                                  'select name from classify where id = %s and (store_id is Null or store_id = %s)',
                                                  (sql_commoidt_data[0][2], data.mall_id))
                out = {
                    'name':mongodb_specification_data['name'],
                    'classify':classify[0][0],
                    'types':mongodb_specification_data['type'],
                    'info':mongodb_specification_data['info'],
                    'specification_list':mongodb_specification_data['specification_list'],
                    'time':mongodb_specification_data.get('time', sql_commoidt_data[0][3] if len(sql_commoidt_data[0]) > 3 else ''),
                }
                img_list = []
                for i in mongodb_specification_data['img_list']:
                    with open(i,'rb') as f:
                        img_list.append(base64.b64encode(f.read()).decode('utf-8'))
                out['img_list'] = img_list
                return {'current':True,'data':out}
            else:
                return {'current':False,'msg':'未查询到该商品上架申请'}
        sel_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
        Verify_data = await verify.run(sel_data)
        if Verify_data['current']:
            return await execute()
        else:
            return {'current':False,'msg':'验证失败','code':401}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))