from typing import Annotated
from datetime import datetime

from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, Form, HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.file_client import read_file_base64_with_cache
from data.data_mods import ManageCommodityAppealQuery, ManageCommodityAppealHandle

router = APIRouter()


@router.get('/manage_commodity_appeal_list')
async def manage_commodity_appeal_list(data: ManageCommodityAppealQuery = Depends(),
                                       access_token: str = Header(...),
                                       db: Connection = Depends(get_db),
                                       redis: RedisClient = Depends(get_redis),
                                       mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """平台端获取商品违规申诉列表"""
    verify = ManagementTokenVerify(token=access_token, redis_client=redis)
    admin_token_content = await verify.token_admin()

    async def execute():
        cache = CacheService(redis)
        page_size = data.page_size
        page = data.page if data.page and data.page > 0 else 1
        offset = (page - 1) * page_size

        cache_key = cache._make_key('admin:commodity:appeal', page, page_size,
                                    data.select_data or '', data.status or '')
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data

        query = {}
        if data.status and data.status.strip():
            query['status'] = data.status.strip()

        if data.select_data and data.select_data.strip():
            query['$or'] = [
                {'reason': {'$regex': data.select_data.strip(), '$options': 'i'}},
                {'applicant': {'$regex': data.select_data.strip(), '$options': 'i'}}
            ]

        total = await mongodb.count_documents('commodity_appeal', query)
        appeal_data = await mongodb.find_many('commodity_appeal', query,
                                              limit=page_size,
                                              skip=offset,
                                              sort=[('appeal_time', -1)])

        out = []
        if appeal_data:
            # 批量获取商品名称和店铺名称
            for item in appeal_data:
                commodity = await mongodb.find_one('shopping', {
                    'mall_id': item.get('mall_id'),
                    'shopping_id': item.get('shopping_id')
                })
                store_data = await execute_db_query(db,
                                                    'SELECT mall_name FROM store WHERE mall_id = %s',
                                                    (item.get('mall_id'),))
                # 获取违规原因
                violation_info = await mongodb.find_one('commodity_violation', {
                    'mall_id': item.get('mall_id'),
                    'shopping_id': item.get('shopping_id')
                })

                status_text = {'pending': '待处理', 'approved': '已通过', 'rejected': '已驳回'}.get(
                    item.get('status', ''), '未知')

                img_path = commodity.get('img_list', [''])[0] if commodity and commodity.get('img_list') else ''
                img = ''
                if img_path:
                    img_b64 = await read_file_base64_with_cache(img_path, redis, cache_expire=3600)
                    if img_b64:
                        img = f'data:image/jpeg;base64,{img_b64}'

                out.append({
                    'appeal_id': item.get('_id', ''),
                    'mall_id': item.get('mall_id'),
                    'shopping_id': item.get('shopping_id'),
                    'commodity_name': commodity.get('name', '未知商品') if commodity else '已删除商品',
                    'mall_name': store_data[0][0] if store_data else '未知店铺',
                    'reason': item.get('reason', ''),
                    'applicant': item.get('applicant', ''),
                    'status': item.get('status', ''),
                    'status_text': status_text,
                    'appeal_time': item.get('appeal_time', ''),
                    'handle_time': item.get('handle_time', ''),
                    'handler': item.get('handler', ''),
                    'remark': item.get('remark', ''),
                    'violation_reason': violation_info.get('reason', '') if violation_info else '',
                    'img': img,
                })

        result = {'current': True, 'appeal_list': out, 'total': total, 'page': page, 'page_size': page_size}
        await cache.set(cache_key, result, expire=30)
        return result

    try:
        sql_data = await execute_db_query(db, 'select user from manage_user where user = %s',
                                          admin_token_content['user'])
        Verify_data = await verify.run(sql_data)
        if Verify_data['current']:
            return await execute()
        else:
            return {'current': False, 'msg': '验证失败', 'code': 401}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/manage_commodity_appeal_handle')
async def manage_commodity_appeal_handle(data: Annotated[ManageCommodityAppealHandle, Form()],
                                         db: Connection = Depends(get_db),
                                         redis: RedisClient = Depends(get_redis),
                                         mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """平台端处理商品违规申诉（通过/驳回）"""
    verify = ManagementTokenVerify(token=data.token, redis_client=redis)
    admin_token_content = await verify.token_admin()

    async def execute():
        # 查找申诉记录
        from bson import ObjectId
        try:
            appeal = await mongodb.find_one('commodity_appeal', {'_id': ObjectId(data.appeal_id)})
        except Exception:
            return {'current': False, 'msg': '申诉ID无效'}

        if not appeal:
            return {'current': False, 'msg': '申诉记录不存在'}

        if appeal.get('status') != 'pending':
            return {'current': False, 'msg': '该申诉已处理'}

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if data.action == 'approve':
            # 通过申诉：恢复商品为已下架状态(3)，可重新上架
            await mongodb.update_one('commodity_appeal',
                                     {'_id': ObjectId(data.appeal_id)},
                                     {'$set': {
                                         'status': 'approved',
                                         'handle_time': now,
                                         'handler': admin_token_content['user'],
                                         'remark': data.remark or '申诉通过'
                                     }})

            mall_id = appeal.get('mall_id')
            shopping_id = appeal.get('shopping_id')

            await execute_db_query(db,
                                   'UPDATE shopping SET audit = %s WHERE mall_id = %s AND shopping_id = %s',
                                   (3, mall_id, shopping_id))
            await mongodb.update_one('shopping',
                                     {'shopping_id': shopping_id},
                                     {'$set': {'audit': 3}})

            # 删除违规记录
            await mongodb.delete_one('commodity_violation', {
                'mall_id': mall_id,
                'shopping_id': shopping_id
            })

            # 通知商家
            await mongodb.insert_one('commodity_msg', {
                'mall_id': mall_id,
                'shopping_id': shopping_id,
                'pass': 5,
                'msg': f'您的商品违规申诉已通过，商品已恢复为下架状态，您可以重新上架。备注：{data.remark or "无"}',
                'auditor': admin_token_content['user'],
                'read': 0
            })

            cache = CacheService(redis)
            await cache.delete_pattern('admin:commodity:*')
            await cache.delete_pattern(f'commodity:list:{mall_id}:*')
            await cache.delete_pattern(f'commodity:inform:*')

            return {'current': True, 'msg': '申诉已通过，商品恢复为下架状态'}

        elif data.action == 'reject':
            # 驳回申诉
            await mongodb.update_one('commodity_appeal',
                                     {'_id': ObjectId(data.appeal_id)},
                                     {'$set': {
                                         'status': 'rejected',
                                         'handle_time': now,
                                         'handler': admin_token_content['user'],
                                         'remark': data.remark or '申诉驳回'
                                     }})

            mall_id = appeal.get('mall_id')
            shopping_id = appeal.get('shopping_id')

            # 通知商家
            await mongodb.insert_one('commodity_msg', {
                'mall_id': mall_id,
                'shopping_id': shopping_id,
                'pass': 6,
                'msg': f'您的商品违规申诉已被驳回。原因：{data.remark or "未说明"}',
                'auditor': admin_token_content['user'],
                'read': 0
            })

            cache = CacheService(redis)
            await cache.delete_pattern('admin:commodity:appeal:*')
            await cache.delete_pattern(f'commodity:inform:*')

            return {'current': True, 'msg': '申诉已驳回'}
        else:
            return {'current': False, 'msg': '无效的操作类型'}

    try:
        if admin_token_content['current']:
            sql_data = await execute_db_query(db, 'select user from manage_user where user = %s',
                                              admin_token_content['user'])
            Verify_data = await verify.run(sql_data)
            if Verify_data['current']:
                return await execute()
            else:
                return {'current': False, 'msg': '验证失败'}
        else:
            return {'current': False, 'msg': '验证失败'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
