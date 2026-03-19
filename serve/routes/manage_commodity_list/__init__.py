from aiomysql import Connection
from fastapi import APIRouter, Depends, Header, HTTPException

from services.management_token_verify import ManagementTokenVerify
from services.cache_service import CacheService

from data.sql_client import get_db, execute_db_query
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client
from data.file_client import read_file_base64_with_cache
from data.data_mods import ManageCommodityListQuery

router = APIRouter()


@router.get('/manage_commodity_list')
async def manage_commodity_list(data: ManageCommodityListQuery = Depends(),
                                access_token: str = Header(...),
                                db: Connection = Depends(get_db),
                                redis: RedisClient = Depends(get_redis),
                                mongodb: MongoDBClient = Depends(get_mongodb_client)):
    """平台端获取商品列表（支持分页、搜索、状态筛选、店铺筛选）"""
    verify = ManagementTokenVerify(token=access_token, redis_client=redis)
    admin_token_content = await verify.token_admin()

    async def execute():
        cache = CacheService(redis)
        page_size = data.page_size
        page = data.page if data.page and data.page > 0 else 1
        offset = (page - 1) * page_size

        # 状态映射：0=待审核 1=上架 3=已下架 4=违规 5=店铺关闭异常状态 其他=审核未通过（从 SQL 读取）
        def audit_to_text(audit_val):
            m = {0: '待审核', 1: '上架', 3: '已下架', 4: '违规', 5: '店铺关闭异常状态'}
            return m.get(audit_val, '审核未通过')

        status_map = {
            'on_sale': 1, 'off_shelf': 3, 'auditing': 0, 'violation': 4, 'store_closed': 5,
            'rejected': None,  # 非 0/1/3/4/5 的为审核未通过
        }

        cache_key = cache._make_key('admin:commodity:list',
                                    page, page_size,
                                    data.select_data or '',
                                    data.status or '',
                                    data.mall_id or '')
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data

        # 从 MongoDB 查匹配的 (mall_id, shopping_id)
        id_pairs = None
        if data.select_data and data.select_data.strip():
            search_filter = {'name': {'$regex': data.select_data.strip(), '$options': 'i'}}
            if data.mall_id:
                search_filter['mall_id'] = data.mall_id
            mongodb_search = await mongodb.find_many('shopping', search_filter)
            if not mongodb_search:
                result = {'current': True, 'commodity_list': [], 'total': 0, 'page': page, 'page_size': page_size}
                return result
            id_pairs = list(set((item['mall_id'], item['shopping_id']) for item in mongodb_search))

        # 构建 SQL 条件（状态从 SQL 读取）
        sql_conditions = []
        sql_params = []
        if data.mall_id:
            sql_conditions.append('mall_id = %s')
            sql_params.append(data.mall_id)
        if data.status and data.status in status_map:
            av = status_map[data.status]
            if av is not None:
                sql_conditions.append('audit = %s')
                sql_params.append(av)
            else:
                sql_conditions.append('audit NOT IN (0, 1, 3, 4, 5)')
        if id_pairs:
            ph = ','.join(['(%s,%s)'] * len(id_pairs))
            sql_conditions.append(f'(mall_id, shopping_id) IN ({ph})')
            for m, s in id_pairs:
                sql_params.extend([m, s])

        where = ' AND '.join(sql_conditions) if sql_conditions else '1=1'

        # 从 SQL 查询
        total = (await execute_db_query(db, f'SELECT COUNT(*) FROM shopping WHERE {where}', tuple(sql_params)))[0][0]
        list_sql = f'''SELECT mall_id, shopping_id, audit, time FROM shopping
                      WHERE {where} ORDER BY time DESC LIMIT %s OFFSET %s'''
        sql_params.extend([page_size, offset])
        sql_rows = await execute_db_query(db, list_sql, tuple(sql_params))

        out = []
        if sql_rows:
            mall_ids = list(set(r[0] for r in sql_rows))
            mall_names = {}
            if mall_ids:
                ph = ','.join(['%s'] * len(mall_ids))
                store_data = await execute_db_query(db, f'SELECT mall_id, mall_name FROM store WHERE mall_id IN ({ph})', tuple(mall_ids))
                for row in store_data:
                    mall_names[row[0]] = row[1]

            for row in sql_rows:
                mall_id, shopping_id, audit_val, time_val = row[0], row[1], row[2], row[3]
                mongo_doc = await mongodb.find_one('shopping', {'mall_id': mall_id, 'shopping_id': shopping_id})
                name = mongo_doc.get('name', '') if mongo_doc else ''
                info = mongo_doc.get('info', '') if mongo_doc else ''
                types = mongo_doc.get('type', []) if mongo_doc else []
                img_list = mongo_doc.get('img_list', []) if mongo_doc else []
                img_path = img_list[0] if img_list else ''
                img = ''
                if img_path:
                    img_b64 = await read_file_base64_with_cache(img_path, redis, cache_expire=3600)
                    if img_b64:
                        img = f'data:image/jpeg;base64,{img_b64}'
                time_str = time_val.strftime('%Y-%m-%d %H:%M:%S') if hasattr(time_val, 'strftime') else str(time_val)
                out.append({
                    'mall_id': mall_id, 'shopping_id': shopping_id, 'name': name, 'info': info, 'types': types,
                    'audit': audit_val, 'audit_text': audit_to_text(audit_val), 'time': time_str,
                    'mall_name': mall_names.get(mall_id, '未知店铺'), 'img': img,
                })

        result = {'current': True, 'commodity_list': out, 'total': total, 'page': page, 'page_size': page_size}
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
