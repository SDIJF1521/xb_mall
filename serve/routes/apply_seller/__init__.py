from typing import Annotated

import aiomysql
from fastapi import APIRouter, Form, HTTPException, Depends

from data.data_mods import ApplyBusiness
from services.apply_seller import ApplySeller
from data.sql_client import get_db, execute_db_query
router = APIRouter()
@router.post('/apply_seller')

async def apply_seller( data:Annotated[ApplyBusiness,Form()], db:aiomysql.Connection = Depends(get_db)) -> dict:
    apply = ApplySeller(name=data.name, phone=data.phone, mall_name=data.mall_name, mall_describe=data.mall_describe)
    database_data = await execute_db_query(db,'select * FROM shop_apply')
    out = await apply.apply(database_data, token=data.token)
    if out['current']:
        await execute_db_query(db, out['query'], out['params'])
        return {'msg': '已提交请求, 我们将在3个工作日内审核您的申请并通过短信通知您。', 'current': True}
    else:
        return {'msg': out['msg'], 'current': False}