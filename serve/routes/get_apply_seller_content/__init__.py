import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form

from data.sql_client import get_db, execute_db_query
from services.apply_seller_conten import ApplySellerConten


router = APIRouter()
@router.post('/get_apply_seller_content')
async def get_apply_seller_content(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db)):
    try:
        apply = ApplySellerConten(token= token)
        sql_data = await execute_db_query(db,'SELECT *FROM shop_apply')
        out = await apply.content(sql_data)
        if out['current']:
            return {
                'name':out['name'],
                'phone':out['phone'],
                'mall_name':out['mall_name'],
                'mall_describe':out['mall_describe'],
                'current':True
            }
        else:
            return {'msg':out['msg'],'current':False}
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")