from typing import Annotated

from aiomysql import connect
from fastapi import APIRouter,Depends,Form,HTTPException
from starlette.responses import Content

from services.management_token_verify import ManagementTokenVerify

from data.data_mods import ManageRejectCommodityApply
from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

# 管理员驳回商品上架申请路由
router = APIRouter()
@router.post('/manage_commodity_rejectAudit')
async def manage_commodity_rejectAudit(data:Annotated[ManageRejectCommodityApply,Form()],
                                        db:Content = Depends(get_db),
                                        redis:RedisClient = Depends(get_redis),
                                        mongodb:MongoDBClient = Depends(get_mongodb_client)):
    verify = ManagementTokenVerify(token=data.token,redis_client=redis)
    admin_tokrn_content = await verify.token_admin()

    async def execute():
        sql_data = await execute_db_query(db,
                                          'select * from shopping where mall_id= %s and shopping_id = %s',
                                          (data.mall_id,data.shopping_id))
        if sql_data:

            # 更新商品状态
            await execute_db_query(db,
                                   'update shopping set audit = %s where mall_id = %s and shopping_id = %s',
                                   (2,data.mall_id,data.shopping_id))
            await mongodb.update_one('shopping',{'shopping_id':data.shopping_id}, {'$set': {'audit': 2}})
            
            mongodb_data_msg = await mongodb.find_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id,'pass':0,'auditor':admin_tokrn_content['user'],'read':0})
            # 更新商品驳回原因
            if mongodb_data_msg:
                await mongodb.update_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id,'pass':0}, {'$set': {'msg': data.reason,'auditor':admin_tokrn_content['user'],'read':0}})
            # 插入商品驳回原因
            else:
                await mongodb.insert_one('commodity_msg',{'mall_id':data.mall_id,'shopping_id':data.shopping_id,'pass':0,'msg':data.reason,'auditor':admin_tokrn_content['user'],'read':0})
            
            return {'msg':'拒绝成功','current':True}
        else:
            return {'msg':'商品不存在','current':False}
    try:
        if admin_tokrn_content['current']:
            verify_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])
            Verify_data = await verify.run(verify_data)
            if Verify_data['current']:
                return await execute()
            else:
                return {'msg':'验证失败','current':False}
        else:
            return {'msg':'验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    except HTTPException as e:
        return {'msg':str(e),'current':False}