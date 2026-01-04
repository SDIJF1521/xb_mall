from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from services.verify_duter_token import VerifyDuterToken
from services.buyer_role_authority import RoleAuthorityService

from data.sql_client import get_db,execute_db_query
from data.redis_client import RedisClient,get_redis
from data.mongodb_client import MongoDBClient,get_mongodb_client

router = APIRouter()

@router.get('/buter_commodity_inform')
async def buter_commodity_inform(access_token:str = Header(...),
                                db:Connection = Depends(get_db),
                                redis:RedisClient = Depends(get_redis),
                                mongodb:MongoDBClient = Depends(get_mongodb_client)):
    """
    获取商品审核通知接口
    流程：Token验证 -> 权限检查 -> 查询未读通知（read=0）-> 关联商品信息
    权限：主商户可查看所有店铺通知，店铺用户需要查询权限[2]
    返回：未读通知列表（包含商品名称、审核状态、审核消息等）
    """
    verify_duter_token = VerifyDuterToken(access_token,redis)
    token_data = await verify_duter_token.token_data()

    async def execute(id_list):
        # 获取所有店铺的未读通知（read=0表示未读）
        mongodb_data = []
        for i in id_list:
            mongodb_data.extend(await mongodb.find_many('commodity_msg',{'mall_id':i,'read':0}))

        if mongodb_data:
            # 为每条通知关联商品详细信息
            result_data = []
            for msg in mongodb_data:
                # 从shopping集合中查询商品信息（商品名称、描述等）
                commodity_info = await mongodb.find_one('shopping', {
                    'mall_id': msg.get('mall_id'),
                    'shopping_id': msg.get('shopping_id')
                })
                
                # 构建返回数据：包含商品名称、内容、审核状态、审核消息、审核人等
                item = {
                    'mall_id': msg.get('mall_id'),
                    'shopping_id': msg.get('shopping_id'),
                    'pass': msg.get('pass'),  # 审核结果：1通过，2驳回
                    'read': msg.get('read'),  # 是否已读：0未读，1已读
                    'name': commodity_info.get('name') if commodity_info else None,
                    'info': commodity_info.get('info') if commodity_info else None,
                    'msg': msg.get('msg'),  # 审核消息
                    'auditor': msg.get('auditor')  # 审核人
                }
                result_data.append(item)
            
            return {'code':200,'msg':'获取成功','current':True,'data':result_data,'flag':True}
        else:
            return {'code':200,'msg':'没有通知','current':True,'flag':False}

    if token_data.get('station') == '1':
        sql_data = await execute_db_query(db,'select user from seller_sing where user = %s',(token_data.get('user')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        if verify_data:
            return await execute(token_data.get('state_id_list'))
        else:
            return {'code':403,'msg':'验证失败','current':False}
    else:
        role_authority_service = RoleAuthorityService(token_data.get('role'),db)
        role_authority = await role_authority_service.get_authority(token_data.get('mall_id'))
        execute_code = await role_authority_service.authority_resolver(int(role_authority[0][0]))
        sql_data = await execute_db_query(db,'select user from store_user where user = %s and store_id = %s',(token_data.get('user'),token_data.get('mall_id')))
        verify_data = await verify_duter_token.verify_token(sql_data)
        # 需要查询权限[2]
        if execute_code[2] and verify_data:
            # 店铺用户只能查看当前店铺的通知
            return await execute([token_data.get('state_id')])
        else:
            return {'code':403,'msg':'您没有权限执行此操作','current':False}