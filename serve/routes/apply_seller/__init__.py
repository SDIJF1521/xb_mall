from typing import Annotated

import aiomysql
from fastapi import APIRouter, Form, HTTPException, Depends

from data.data_mods import ApplyBusiness
from services.apply_seller import ApplySeller
from data.sql_client import get_db, execute_db_query
router = APIRouter()

@router.post('/apply_seller')
async def apply_seller( data:Annotated[ApplyBusiness,Form()], db:aiomysql.Connection = Depends(get_db)) -> dict:
    """
    申请成为商户接口
    流程：Token验证 -> 检查是否已申请 -> 插入申请记录（状态：待审核）
    """
    apply = ApplySeller(name=data.name, phone=data.phone, mall_name=data.mall_name, mall_describe=data.mall_describe)
    # 获取所有申请记录，用于检查重复申请
    database_data = await execute_db_query(db,'select * FROM shop_apply')
    # 执行申请业务逻辑（Token验证、重复申请检查等）
    out = await apply.apply(database_data, token=data.token)
    if out['current']:
        # 申请成功，插入申请记录到数据库
        await execute_db_query(db, out['query'], out['params'])
        return {'msg': '已提交请求, 我们将在3个工作日内审核您的申请并通过短信通知您。', 'current': True}
    else:
        return {'msg': out['msg'], 'current': False}