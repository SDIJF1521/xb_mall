"""GET /browsing_history 获取用户浏览记录列表（需登录，分页）"""
import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from services.record import Record
from services.user_info import UserInfo
from data.redis_client import get_redis, RedisClient
from data.file_client import read_file_base64_with_cache
from data.mongodb_client import get_mongodb_client, MongoDBClient

router = APIRouter()

_PAGE_SIZE = 10


@router.get('/browsing_history')
async def browsing_history(
    page: int = Query(1, ge=1, description='页码，从1开始'),
    access_token: Annotated[str | None, Header()] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取当前登录用户的浏览记录，按最近浏览时间降序，每页10条。"""
    if not access_token:
        return {'code': 401, 'msg': '请先登录', 'success': False}

    user_info = UserInfo(access_token)
    verify = await user_info.token_analysis()
    if not verify.get('current'):
        return {'code': 401, 'msg': verify.get('msg', 'token无效'), 'success': False}

    user = verify['user']
    recorder = Record(mongodb, redis_client=redis)

    all_records = await recorder.get_user_records(user, limit=1000)
    total = len(all_records)
    start = (page - 1) * _PAGE_SIZE
    page_records = all_records[start: start + _PAGE_SIZE]

    if not page_records:
        return {
            'code': 200, 'msg': '成功', 'success': True,
            'total': total, 'page': page, 'page_size': _PAGE_SIZE, 'data': [],
        }

    async def _build_item(record: dict) -> dict | None:
        shopping_id = record.get('shopping_id') or record.get('commodity_id')
        mall_id = record.get('mall_id')
        if shopping_id is None:
            return None

        product = await mongodb.find_one('shopping', {'shopping_id': int(shopping_id)})
        if not product:
            return {
                'shopping_id': shopping_id,
                'mall_id': mall_id,
                'name': '商品已下架',
                'img': '',
                'price': 0,
                'type': [],
                'browse_count': record.get('browse_count', record.get('count', 0)),
                'last_browse_at': record.get('updated_at', ''),
                'available': False,
            }

        spec_list = product.get('specification_list') or []
        price = float(spec_list[0].get('price', 0)) if spec_list else 0.0
        img_list = product.get('img_list') or []

        img_b64 = ''
        if img_list:
            img_b64 = await read_file_base64_with_cache(img_list[0], redis, cache_expire=3600) or ''

        return {
            'shopping_id': product.get('shopping_id'),
            'mall_id': product.get('mall_id'),
            'name': product.get('name', ''),
            'img': img_b64,
            'price': price,
            'type': product.get('type', []),
            'browse_count': record.get('browse_count', record.get('count', 0)),
            'last_browse_at': record.get('updated_at', ''),
            'available': product.get('audit') == 1,
        }

    results = await asyncio.gather(*[_build_item(r) for r in page_records])
    items = [item for item in results if item is not None]

    return {
        'code': 200, 'msg': '成功', 'success': True,
        'total': total, 'page': page, 'page_size': _PAGE_SIZE, 'data': items,
    }
