"""GET /commodity_detail 获取商品详情（登录后记录浏览行为，供推荐模型训练）"""
import asyncio
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Header

from config.log_config import logger
from services.user_info import UserInfo
from services.record import Record
from data.redis_client import get_redis, RedisClient
from data.file_client import read_file_base64_with_cache
from data.mongodb_client import get_mongodb_client, MongoDBClient
from data.sql_client_pool import db_pool

router = APIRouter()


async def _record_browse(
    user: str,
    shopping_id: int,
    mall_id: int,
    mongodb: MongoDBClient,
    redis: RedisClient,
):
    """记录用户浏览行为（供推荐模型训练使用），写入失败不影响主流程"""
    try:
        logger.info(f"[浏览记录] 开始写入 user={user} shopping_id={shopping_id} mall_id={mall_id}")
        recorder = Record(mongodb, redis_client=redis)
        result = await recorder.browse_record(user, shopping_id, mall_id)
        logger.info(f"[浏览记录] 写入结果={result} user={user} shopping_id={shopping_id}")
    except Exception as e:
        logger.error(f"[浏览记录] 写入异常 user={user} shopping_id={shopping_id} error={e}")


@router.get('/commodity_detail')
async def commodity_detail(
    background_tasks: BackgroundTasks,
    mall_id: int = Query(..., description='店铺ID'),
    shopping_id: int = Query(..., description='商品ID'),
    access_token: Annotated[str, Header()] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """获取商品详情（无需登录，登录后异步记录浏览行为）"""
    doc = await mongodb.find_one(
        'shopping',
        {'mall_id': mall_id, 'shopping_id': shopping_id, 'audit': 1},
    )
    if not doc:
        return {'code': 404, 'msg': '商品不存在或已下架', 'success': False}

    img_tasks = [
        read_file_base64_with_cache(path, redis, cache_expire=3600)
        for path in doc.get('img_list', [])
    ]
    img_list = await asyncio.gather(*img_tasks)

    if access_token:
        user_info = UserInfo(access_token)
        verify = await user_info.token_analysis()
        logger.info(f"[商品详情] token验证结果={verify} shopping_id={shopping_id}")
        if verify.get('current'):
            logger.info(f"[商品详情] 触发浏览记录 user={verify['user']} shopping_id={shopping_id}")
            background_tasks.add_task(
                _record_browse, verify['user'], shopping_id, mall_id, mongodb, redis
            )
    else:
        logger.info(f"[商品详情] 未携带token(未登录) shopping_id={shopping_id}")

    import json as _json

    # 查询该商品当前所有生效的活动（去掉 LIMIT 1，支持多活动叠加）
    activity_rows = await db_pool.execute_query(
        """SELECT ap.specification_id, ap.activity_price,
                  a.id AS activity_id, a.name AS activity_name,
                  a.activity_type, a.rules, a.end_time, a.issuer_type
           FROM activity_products ap
           JOIN activities a ON ap.activity_id = a.id
           WHERE ap.shopping_id = %s AND ap.mall_id = %s
             AND ap.status = 'active'
             AND a.status = 'active'
             AND NOW() BETWEEN a.start_time AND a.end_time
           ORDER BY a.issuer_type DESC, a.id ASC""",
        (shopping_id, mall_id),
    )

    _RULE_PRICED = {"flash_sale", "discount", "group_buy"}
    _CART_LEVEL  = {"full_reduction"}

    # 解析所有活动行
    parsed_rows = []
    seen_activity_ids = set()
    activities_info = []   # 用于前端展示的活动列表（按 activity_id 去重）

    for row in (activity_rows or []):
        ap_spec_id, act_price, act_id, act_name, act_type, rules_raw, end_time, issuer = row
        try:
            rules = _json.loads(rules_raw) if isinstance(rules_raw, str) else (rules_raw or {})
        except Exception:
            rules = {}
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(end_time, "strftime") else str(end_time)
        parsed_rows.append({
            "spec_id": ap_spec_id,
            "act_price": float(act_price) if act_price is not None else None,
            "act_id": act_id,
            "act_name": act_name,
            "act_type": act_type,
            "rules": rules,
            "end_time": end_time_str,
            "issuer": issuer,
        })
        if act_id not in seen_activity_ids:
            seen_activity_ids.add(act_id)
            activities_info.append({
                "activity_name": act_name,
                "activity_type": act_type,
                "discount_rate": rules.get("discount_rate"),
                "rules": rules,
                "end_time": end_time_str,
                "issuer_type": issuer,
            })

    def _compute_spec_price(original: float, spec_id) -> float | None:
        """
        对一个规格叠加所有适用的活动折扣：
        - 所有 discount_rate 类活动的折扣率连乘
        - full_reduction 不改单价（订单层面处理）
        - 若无任何折扣类活动则返回 None
        """
        combined_rate = 1.0
        has_discount = False
        for r in parsed_rows:
            # 跳过仅针对其他规格的活动行
            if r["spec_id"] is not None and r["spec_id"] != spec_id:
                continue
            if r["act_type"] in _RULE_PRICED:
                dr = r["rules"].get("discount_rate")
                if dr is not None:
                    combined_rate *= float(dr)
                    has_discount = True
            elif r["act_type"] not in _CART_LEVEL and r["act_price"] is not None:
                # 自由定价活动：取最低的显式活动价
                explicit = r["act_price"] / original if original else 1.0
                combined_rate = min(combined_rate, explicit)
                has_discount = True
        if not has_discount:
            return None
        return max(round(original * combined_rate, 2), 0.01)

    # 将叠加后价格写入 specification_list
    spec_list = doc.get('specification_list', [])
    for spec in spec_list:
        sid = spec.get('specification_id') or spec.get('id')
        original = float(spec.get('price', 0))
        eff = _compute_spec_price(original, sid)
        if eff is not None and eff < original:
            spec['original_price'] = original
            spec['price'] = eff

    return {
        'code': 200,
        'msg': '成功',
        'success': True,
        'data': {
            'mall_id': doc['mall_id'],
            'shopping_id': doc['shopping_id'],
            'name': doc.get('name', ''),
            'info': doc.get('info', ''),
            'type': doc.get('type', []),
            'img_list': [img for img in img_list if img],
            'specification_list': spec_list,
            'activities': activities_info,
        },
    }
