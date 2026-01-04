import aiomysql
from fastapi import APIRouter, Depends, HTTPException, Form

from data.sql_client import get_db, execute_db_query
from services.apply_seller_conten import ApplySellerConten
from services.user_info import UserInfo

router = APIRouter()

@router.post('/get_apply_seller_content')
async def get_apply_seller_content(token:str=Form(min_length=6), db:aiomysql.Connection = Depends(get_db)):
    """
    获取用户商户申请详情接口
    流程：Token验证 -> 查询申请信息 -> 如果被驳回则查询驳回原因
    用途：用户查看自己的商户申请状态和驳回原因
    """
    try:
        apply = ApplySellerConten(token= token)
        user = UserInfo(token)
        name = await user.token_analysis()
        if name['current']:
            # 查询用户的商户申请信息
            sql_data = await execute_db_query(db,'SELECT * FROM shop_apply WHERE user = %s',name['user'])
            reject_cause = None
            out = await apply.content(sql_data)
            # 如果申请被驳回（state=2），查询驳回原因
            if out['state'] == 2:
                reject_cause_sql = await execute_db_query(db,'SELECT * FROM rejection_reason WHERE user = %s',name['user'])
                reject_cause = reject_cause_sql[0][1]
            return {
                'name':out['name'],
                'phone':out['phone'],
                'mall_name':out['mall_name'],
                'mall_describe':out['mall_describe'],
                'reject_cause':reject_cause,
                'current':True
            }
        else:
            return {'msg':'token验证失败','current':False}
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")