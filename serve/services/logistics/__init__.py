import httpx
import json
import hashlib
import base64
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from services.cache_service import CacheService
from data.sql_client_pool import DatabasePool
from data.mongodb_client import MongoDBClient
from data.redis_client import RedisClient

logger = logging.getLogger(__name__)


class LogisticsService:
    def __init__(self, db: DatabasePool, mongo: MongoDBClient, redis: RedisClient):
        self.db = db
        self.mongo = mongo
        self.cache = CacheService(redis)
        self.limits = httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=30.0
        )
        self.sandbox = 'https://sfapi-sbox.sf-express.com/std/service'
        self.production = 'https://bspgw.sf-express.com/std/service'
        self.service_code_order = 'EXP_RECE_CREATE_ORDER'
        self.service_code_routes = 'EXP_RECE_SEARCH_ROUTES'

    # ════════════════════ 配置管理 ════════════════════

    async def config(self, user_code: str, code: str, production_environment: bool):
        config_data = await self.mongo.find_one('LogisticsServiceConfig', {'user_code': user_code})
        if config_data:
            await self.mongo.update_one(
                'LogisticsServiceConfig',
                {'user_code': user_code},
                {'$set': {'production_environment': production_environment, 'code': code}},
            )
            await self.cache.delete_pattern("logistics_config")
            return {'code': 200, 'msg': '更新成功', 'success': True}
        else:
            await self.mongo.delete_many('LogisticsServiceConfig', {})
            await self.mongo.insert_one(
                'LogisticsServiceConfig',
                {'user_code': user_code, 'production_environment': production_environment, 'code': code},
            )
            await self.cache.delete_pattern("logistics_config")
            return {'code': 200, 'msg': '配置已创建', 'success': True}

    async def get_config(self):
        config_data = await self.cache.get("logistics_config")
        if config_data:
            return {'code': 200, 'msg': '获取成功', 'success': True, 'data': config_data}
        mongo_config = await self.mongo.find_one('LogisticsServiceConfig', {})
        if not mongo_config:
            return {'code': 404, 'msg': '配置不存在', 'success': False}
        await self.cache.set("logistics_config", mongo_config, expire=3600)
        return {'code': 200, 'msg': '获取成功', 'success': True, 'data': mongo_config}

    # ════════════════════ 连通性测试 ════════════════════

    async def verify_connection(self) -> dict:
        """向顺丰 API 发送一个轻量级查询请求来验证配置是否正确、网络是否可达。"""
        sf_config = await self._get_sf_config()
        if not sf_config:
            return {"success": False, "msg": "尚未配置物流信息，请先录入配置"}

        partner_id = sf_config.get("user_code")
        check_word = sf_config.get("code")
        if not partner_id or not check_word:
            return {"success": False, "msg": "配置不完整：客户编码或校验码缺失"}

        is_production = sf_config.get("production_environment", False)
        env_label = "生产环境" if is_production else "沙箱环境"

        result = await self._call_sf_api(
            self.service_code_routes,
            {"trackingType": "1", "trackingNumber": "SF0000000000", "methodType": "1"},
        )

        if result.get("code") == 504:
            return {"success": False, "msg": f"连接超时：无法访问顺丰{env_label}接口"}
        if not result.get("success"):
            return {"success": False, "msg": result.get("msg", "连接失败")}

        response_data = result.get("data", {})
        api_result_code = response_data.get("apiResultCode", "")

        if api_result_code == "A1001":
            return {"success": False, "msg": f"认证失败：客户编码或校验码不正确（{env_label}）"}
        if api_result_code == "A1000":
            return {"success": True, "msg": f"连通性验证通过（{env_label}）"}

        return {
            "success": True,
            "msg": f"接口可达（{env_label}），返回码：{api_result_code}",
        }

    # ════════════════════ 顺丰 API 基础设施 ════════════════════

    async def _get_sf_config(self) -> dict | None:
        cached = await self.cache.get("logistics_config")
        if cached:
            return cached
        config = await self.mongo.find_one("LogisticsServiceConfig", {})
        if config:
            await self.cache.set("logistics_config", config, expire=3600)
        return config

    def _sign(self, msg_data_str: str, check_word: str) -> str:
        sign_str = f"{msg_data_str}{check_word}"
        md5_obj = hashlib.md5(sign_str.encode("utf-8"))
        return base64.b64encode(md5_obj.digest()).decode("utf-8")

    async def _call_sf_api(self, service_code: str, msg_data: dict) -> dict:
        sf_config = await self._get_sf_config()
        if not sf_config:
            return {'code': 500, 'msg': '没有检测到物流配置，请联系平台管理员', 'success': False}

        partner_id = sf_config.get("user_code")
        check_word = sf_config.get("code")
        is_production = sf_config.get("production_environment", False)

        if not partner_id or not check_word:
            return {'code': 500, 'msg': '顺丰配置不完整（客户编码/校验码为必填）', 'success': False}

        msg_data_str = json.dumps(msg_data, ensure_ascii=False)
        request_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp() * 1000)
        msg_digest = self._sign(msg_data_str, check_word)

        form_data = {
            "partnerID": partner_id,
            "requestID": request_id,
            "serviceCode": service_code,
            "timestamp": timestamp,
            "msgDigest": msg_digest,
            "msgData": msg_data_str,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        url = self.production if is_production else self.sandbox

        try:
            async with httpx.AsyncClient(limits=self.limits, timeout=30.0) as client:
                response = await client.post(url=url, headers=headers, data=form_data, follow_redirects=True)
            response_data = response.json()
            return {
                "code": 200,
                "success": True,
                "data": response_data,
                "request_id": request_id,
            }
        except httpx.TimeoutException:
            return {"code": 504, "msg": "顺丰接口请求超时", "success": False, "request_id": request_id}
        except json.JSONDecodeError:
            return {"code": 500, "msg": "顺丰接口返回非JSON格式数据", "success": False, "request_id": request_id}
        except Exception as e:
            return {"code": 500, "msg": f"请求异常：{str(e)}", "success": False, "request_id": request_id}

    # ════════════════════ 顺丰下单 ════════════════════

    async def place_an_order(
        self,
        order_number: str,
        ship_address: str,
        shipping_address: str,
        addresser_post_code: str,
        recipients_post_code: str,
        product_name: str,
        addresser_tel: str,
        recipients_tel: str,
        sender_name: str = "发件人",
        receiver_name: str = "收件人",
        weight: float = 1.0,
        count: int = 1,
        amount: float = 0,
        currency: str = "CNY",
        sourceArea: str = "CHN",
        unit: str = "个"
    ) -> Dict[str, Any]:
        msg_data = {
            "cargoDetails": [
                {
                    "count": count,
                    "unit": unit,
                    "weight": weight,
                    "amount": amount,
                    "currency": currency,
                    "name": product_name,
                    "sourceArea": sourceArea,
                }
            ],
            "contactInfoList": [
                {
                    "address": ship_address,
                    "contact": sender_name,
                    "contactType": 1,
                    "country": "CN",
                    "postCode": addresser_post_code,
                    "tel": addresser_tel,
                },
                {
                    "address": shipping_address,
                    "contact": receiver_name,
                    "contactType": 2,
                    "country": "CN",
                    "postCode": recipients_post_code,
                    "tel": recipients_tel,
                },
            ],
            "language": "zh_CN",
            "orderId": order_number,
        }

        result = await self._call_sf_api(self.service_code_order, msg_data)
        if not result.get("success"):
            return result

        response_data = result.get("data", {})
        api_result_code = response_data.get("apiResultCode", "")
        api_error_msg = response_data.get("apiErrorMsg", "接口请求异常")
        request_id = result.get("request_id", "")

        if api_result_code == "A1000":
            api_result_data = response_data.get("apiResultData", {})
            if isinstance(api_result_data, str):
                api_result_data = json.loads(api_result_data)
            business_success = api_result_data.get("success", False)
            business_msg = api_result_data.get("errorMsg", api_error_msg)
            waybill_list = api_result_data.get("msgData", {}).get("waybillNoInfoList", [])
            return {
                "code": 200 if business_success else 400,
                "msg": business_msg if business_msg else "下单成功",
                "success": business_success,
                "data": api_result_data,
                "request_id": request_id,
                "waybill_list": waybill_list,
            }
        else:
            return {
                "code": 400,
                "msg": f"顺丰接口校验失败：{api_error_msg}（错误码：{api_result_code}）",
                "success": False,
                "data": response_data,
                "request_id": request_id,
            }

    # ════════════════════ 顺丰物流轨迹查询 ════════════════════

    async def query_routes(self, tracking_number: str) -> dict:
        msg_data = {
            "trackingType": "1",
            "trackingNumber": tracking_number,
            "methodType": "1",
        }
        result = await self._call_sf_api(self.service_code_routes, msg_data)
        if not result.get("success"):
            return result

        response_data = result.get("data", {})
        api_result_code = response_data.get("apiResultCode", "")

        if api_result_code == "A1000":
            api_result_data = response_data.get("apiResultData", {})
            if isinstance(api_result_data, str):
                api_result_data = json.loads(api_result_data)
            return {
                "code": 200,
                "success": True,
                "msg": "查询成功",
                "data": api_result_data,
                "request_id": result.get("request_id"),
            }
        else:
            error_msg = response_data.get("apiErrorMsg", "查询失败")
            return {
                "code": 400,
                "success": False,
                "msg": f"顺丰接口返回错误：{error_msg}（{api_result_code}）",
                "data": response_data,
                "request_id": result.get("request_id"),
            }

    # ════════════════════ 卖家发货 ════════════════════

    async def ship_order(
        self,
        order_no: str,
        mall_id: int,
        sender_name: str,
        sender_phone: str,
        sender_address: str,
        sender_post_code: str = "000000",
    ) -> dict:
        order_rows = await self.db.execute_query(
            "SELECT id, order_no, mall_id, status, receiver_name, receiver_phone, receiver_addr "
            "FROM orders WHERE order_no = %s AND mall_id = %s",
            (order_no, mall_id),
        )
        if not order_rows:
            return {"success": False, "msg": "订单不存在或不属于该店铺"}

        o_id, o_no, o_mall, o_status, recv_name, recv_phone, recv_addr = order_rows[0]
        if o_status != "paid":
            return {"success": False, "msg": f"订单状态为 {o_status}，仅已支付的订单可发货"}

        existing = await self.db.execute_query(
            "SELECT id FROM order_logistics WHERE order_no = %s", (order_no,)
        )
        if existing:
            return {"success": False, "msg": "该订单已发货，请勿重复操作"}

        items = await self.db.execute_query(
            "SELECT product_name, quantity FROM order_items WHERE order_no = %s", (order_no,)
        )
        product_names = ", ".join([f"{it[0]}x{it[1]}" for it in (items or [])[:3]])

        sf_result = await self.place_an_order(
            order_number=order_no,
            ship_address=sender_address,
            shipping_address=recv_addr or "",
            addresser_post_code=sender_post_code,
            recipients_post_code="000000",
            product_name=product_names or "商品",
            addresser_tel=sender_phone,
            recipients_tel=recv_phone or "",
            sender_name=sender_name,
            receiver_name=recv_name or "",
        )

        waybill_no = ""
        if sf_result.get("success") and sf_result.get("waybill_list"):
            for wb in sf_result["waybill_list"]:
                if wb.get("waybillNo"):
                    waybill_no = wb["waybillNo"]
                    break

        if not waybill_no:
            waybill_no = f"SF{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

        await self.db.execute_query(
            """INSERT INTO order_logistics
               (order_no, mall_id, express_company, tracking_number,
                sender_name, sender_phone, sender_address, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (order_no, mall_id, "顺丰速运", waybill_no,
             sender_name, sender_phone, sender_address, "shipped"),
        )

        await self.db.execute_query(
            "UPDATE orders SET status = 'shipped', shipped_at = NOW(), version = version + 1 "
            "WHERE order_no = %s AND status = 'paid'",
            (order_no,),
        )

        return {
            "success": True,
            "msg": "发货成功",
            "tracking_number": waybill_no,
            "express_company": "顺丰速运",
        }

    # ════════════════════ 查询订单物流 ════════════════════

    async def get_logistics_by_order(self, order_no: str) -> dict:
        rows = await self.db.execute_query(
            """SELECT id, order_no, mall_id, express_company, tracking_number,
                      sender_name, sender_phone, sender_address, status,
                      created_at, updated_at
               FROM order_logistics WHERE order_no = %s
               ORDER BY created_at DESC LIMIT 1""",
            (order_no,),
        )
        if not rows:
            return {"success": False, "msg": "暂无物流信息"}

        r = rows[0]
        logistics_info = {
            "id": r[0],
            "order_no": r[1],
            "mall_id": r[2],
            "express_company": r[3],
            "tracking_number": r[4],
            "sender_name": r[5],
            "sender_phone": r[6],
            "sender_address": r[7],
            "status": r[8],
            "created_at": str(r[9]) if r[9] else None,
            "updated_at": str(r[10]) if r[10] else None,
            "routes": None,
        }

        if r[4]:
            try:
                routes_result = await self.query_routes(r[4])
                if routes_result.get("success"):
                    logistics_info["routes"] = routes_result.get("data", {})
            except Exception as e:
                logger.warning("查询物流轨迹失败: %s", e)

        return {"success": True, "data": logistics_info}

    # ════════════════════ 卖家物流列表 ════════════════════

    async def get_logistics_list(
        self, mall_id: int, keyword: str | None, page: int, page_size: int
    ) -> dict:
        offset = (page - 1) * page_size
        where = "WHERE ol.mall_id = %s"
        params: list = [mall_id]

        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            where += " AND (ol.order_no LIKE %s OR ol.tracking_number LIKE %s)"
            params.extend([kw, kw])

        count_rows = await self.db.execute_query(
            f"SELECT COUNT(*) FROM order_logistics ol {where}", tuple(params)
        )
        total = count_rows[0][0] if count_rows else 0

        rows = await self.db.execute_query(
            f"""SELECT ol.id, ol.order_no, ol.mall_id, ol.express_company,
                       ol.tracking_number, ol.sender_name, ol.sender_phone,
                       ol.sender_address, ol.status, ol.created_at,
                       o.receiver_name, o.receiver_phone, o.receiver_addr,
                       o.total_amount, o.status AS order_status
                FROM order_logistics ol
                LEFT JOIN orders o ON ol.order_no = o.order_no
                {where}
                ORDER BY ol.created_at DESC
                LIMIT %s OFFSET %s""",
            tuple(params + [page_size, offset]),
        )

        data = []
        for r in (rows or []):
            data.append({
                "id": r[0], "order_no": r[1], "mall_id": r[2],
                "express_company": r[3], "tracking_number": r[4],
                "sender_name": r[5], "sender_phone": r[6],
                "sender_address": r[7], "status": r[8],
                "created_at": str(r[9]) if r[9] else None,
                "receiver_name": r[10], "receiver_phone": r[11],
                "receiver_addr": r[12],
                "total_amount": float(r[13]) if r[13] else None,
                "order_status": r[14],
            })

        return {
            "success": True, "total": total,
            "page": page, "page_size": page_size,
            "data": data,
        }

