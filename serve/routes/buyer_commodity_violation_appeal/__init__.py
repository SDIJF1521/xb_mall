from typing import Annotated, Optional
from datetime import datetime

from aiomysql import Connection
from fastapi import APIRouter, Depends, Form, Header, Query, HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService
from services.cache_service import CacheService

from data.data_mods import BuyerCommodityViolationAppeal
from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()


@router.get('/buyer_commodity_appeal_status')
async def buyer_commodity_appeal_status(stroe_id: int = Query(...),
                                        shopping_id: int = Query(...),
                                        access_token: str = Header(..., alias='access-token'),
                                        redis: RedisClient = Depends(get_redis),
                                        mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """商家端查询商品申诉状态"""
    verify_duter_token = VerifyDuterToken(access_token, redis)
    token_data = await verify_duter_token.token_data()

    if token_data is None:
        return {"code": 403, "msg": "无效的token", 'current': False}

    try:
        violation_info = await mongodb.find_one('commodity_violation', {
            'mall_id': stroe_id,
            'shopping_id': shopping_id
        })
        violation_reason = violation_info.get('reason', '') if violation_info else ''

        appeal_list = await mongodb.find_many('commodity_appeal', {
            'mall_id': stroe_id,
            'shopping_id': shopping_id,
        }, sort=[('appeal_time', -1)], limit=1)
        appeal = appeal_list[0] if appeal_list else None

        if not appeal:
            return {
                "code": 200, "current": True, "has_appeal": False,
                "violation_reason": violation_reason, "data": None
            }

        status_text = {'pending': '待处理', 'approved': '已通过', 'rejected': '已驳回'}.get(
            appeal.get('status', ''), '未知')

        return {
            "code": 200,
            "current": True,
            "has_appeal": True,
            "violation_reason": violation_reason,
            "data": {
                "status": appeal.get('status', ''),
                "status_text": status_text,
                "reason": appeal.get('reason', ''),
                "appeal_time": appeal.get('appeal_time', ''),
                "handle_time": appeal.get('handle_time', ''),
                "remark": appeal.get('remark', ''),
                "violation_reason": violation_reason
            }
        }
    except Exception as e:
        return {"code": 500, "msg": str(e), 'current': False}


@router.post('/buyer_commodity_violation_appeal')
async def buyer_commodity_violation_appeal(data: Annotated[BuyerCommodityViolationAppeal, Form()],
                                           db: Connection = Depends(get_db),
                                           redis: RedisClient = Depends(get_redis),
                                           mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """商家端提交违规商品申诉"""
    verify_duter_token = VerifyDuterToken(data.token, redis)
    token_data = await verify_duter_token.token_data()

    if token_data is None:
        return {"code": 403, "msg": "无效的token", 'current': False}

    async def execute():
        # 检查商品是否存在且为违规状态
        sql_data = await execute_db_query(db,
                                          'SELECT * FROM shopping WHERE mall_id = %s AND shopping_id = %s AND audit = 4',
                                          (data.stroe_id, data.shopping_id))
        if not sql_data:
            return {"code": 404, "msg": "商品不存在或不是违规状态", 'current': False}

        # 检查是否有待处理的申诉
        existing_appeal = await mongodb.find_one('commodity_appeal', {
            'mall_id': data.stroe_id,
            'shopping_id': data.shopping_id,
            'status': 'pending'
        })
        if existing_appeal:
            return {"code": 400, "msg": "该商品已有待处理的申诉，请等待审核", 'current': False}

        # 插入申诉记录
        await mongodb.insert_one('commodity_appeal', {
            'mall_id': data.stroe_id,
            'shopping_id': data.shopping_id,
            'reason': data.reason,
            'applicant': token_data.get('user'),
            'status': 'pending',
            'appeal_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'handle_time': None,
            'handler': None,
            'remark': None
        })

        cache = CacheService(redis)
        await cache.delete_pattern('admin:commodity:appeal:*')

        return {"code": 200, "msg": "申诉已提交，请等待平台审核", 'current': True}

    try:
        if token_data.get('station') == '1':
            sql_data = await execute_db_query(db, 'select user from seller_sing where user = %s',
                                              (token_data.get('user')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data[0]:
                if data.stroe_id not in token_data.get('state_id_list'):
                    return {'code': 400, 'msg': '权限不足', 'current': False}
                return await execute()
            else:
                return {"code": 403, "msg": "验证失败", 'current': False}
        else:
            role_authority_service = RoleAuthorityService(role=token_data.get('role'),
                                                         db=db,
                                                         redis=redis,
                                                         name=token_data.get('user'),
                                                         mall_id=token_data.get('mall_id'))
            role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
            execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
            sql_data = await execute_db_query(db, 'select user from store_user where user = %s and store_id = %s',
                                              (token_data.get('user'), token_data.get('mall_id')))
            verify_data = await verify_duter_token.verify_token(sql_data)
            if verify_data[0]:
                if data.stroe_id != token_data.get('mall_id'):
                    return {'code': 400, 'msg': '权限不足', 'current': False}
                return await execute()
            else:
                return {"code": 403, "msg": "您没有权限执行此操作", 'current': False}
    except Exception as e:
        return {"code": 500, "msg": str(e), 'current': False}
