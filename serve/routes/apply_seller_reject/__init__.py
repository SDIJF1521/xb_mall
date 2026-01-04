from typing import Annotated

import aiomysql
from fastapi import APIRouter, Depends, Form, HTTPException

from services.management_token_verify import ManagementTokenVerify
from data.data_mods import ApplySellerReject
from data.redis_client import RedisClient,get_redis
from data.sql_client import get_db, execute_db_query


router = APIRouter()

@router.post('/apply_seller_reject')
async def apply_seller_reject(data:Annotated[ApplySellerReject,Form()], db:aiomysql.Connection = Depends(get_db),redis_client:RedisClient=Depends(get_redis)):
    """
    管理员驳回商户申请接口
    流程：管理员Token验证 -> 更新申请状态为2（驳回）-> 保存驳回原因
    """
    try:
        verify = ManagementTokenVerify(token=data.token,redis_client=redis_client)
        admin_tokrn_content = await verify.token_admin()
        if admin_tokrn_content['current']:
            verify_data = await execute_db_query(db,'select user from manage_user where user = %s',admin_tokrn_content['user'])

            Verify_data = await verify.run(verify_data)
            if Verify_data['current']:
                # 检查是否已有驳回记录
                reject_user_list = await execute_db_query(db,'select user from rejection_reason where user = %s',data.name)
                if reject_user_list:
                    # 更新驳回原因和申请状态（state=2表示驳回）
                    await execute_db_query(db,'update rejection_reason set reason=%s where user = %s',(data.reason,data.name))
                    await execute_db_query(db,'update shop_apply set state=%s where user = %s',(2,data.name))
                    return {'msg':'拒绝成功','current':True}
                else:
                    # 插入驳回原因和更新申请状态
                    await execute_db_query(db,'update shop_apply set state=%s where user = %s',(2,data.name))
                    await execute_db_query(db,'insert into rejection_reason(user,reason) values(%s,%s)',(data.name,data.reason))
                    return {'msg':'拒绝成功','current':True}
            else:
                return {'msg':'验证失败','current':False}
        else:
            return {'msg':'验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
