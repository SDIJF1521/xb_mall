import httpx
import json
import hashlib
import base64
import uuid
from datetime import datetime
from typing import Dict, Any

from services.cache_service import CacheService
from data.sql_client_pool import DatabasePool
from data.mongodb_client import MongoDBClient
from data.redis_client import RedisClient

# 定义物流服务类
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
        # 顺丰接口地址（文档标准，无后缀）
        self.sandbox = 'https://sfapi-sbox.sf-express.com/std/service'
        self.production = 'https://bspgw.sf-express.com/std/service'
        # 顺丰接口服务代码
        self.service_code = 'EXP_RECE_CREATE_ORDER'
        self.cache = CacheService(redis)

    # 定义物流配置方法
    async def config(self, user_code: str, code: str, production_environment: bool):
        config_data = await self.mongo.find_one('LogisticsServiceConfig',{'user_code':user_code})
        if config_data:
            await self.mongo.update_one('LogisticsServiceConfig',{'user_code':user_code},{'$set': {'production_environment':production_environment,'code':code}})
            await self.cache.delete_pattern(f"logistics_config")
            return {'code': 200, 'msg': '更新成功', 'success': True}
        else:
            await self.mongo.delete_many('LogisticsServiceConfig',{})  # 确保只有一条配置
            await self.mongo.insert_one('LogisticsServiceConfig',{'user_code':user_code,'production_environment':production_environment,'code':code})   
            await self.cache.delete_pattern(f"logistics_config")
            return {'code': 200, 'msg': '配置已创建', 'success': True}

    # 定义获取物流配置方法
    async def get_config(self):
        config_data = await self.cache.get(f"logistics_config")
        if config_data:
            return {'code': 200, 'msg': '获取成功', 'success': True, 'data': config_data}
        else:
            mongo_config = await self.mongo.find_one('LogisticsServiceConfig',{})
            if not mongo_config:
                return {'code': 404, 'msg': '配置不存在', 'success': False}
            await self.cache.set("logistics_config", mongo_config, expire=3600)  # 缓存1小时
            return {'code': 200, 'msg': '获取成功', 'success': True, 'data': mongo_config}
        
    # 定义物流下单方法
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
        sender_name: str = "小曾",
        receiver_name: str = "小邱",
        weight: float = 6.1,
        count: int = 1,
        amount: float = 100.5111,
        currency: str = "HKD",
        sourceArea: str = "CHN",
        unit: str = "个"
    ) -> Dict[str, Any]:
        '''
        下单方法
         :param order_number: 订单号
         :param ship_address: 发货地址
         :param shipping_address: 收货地址
         :param addresser_post_code: 发件人邮编
         :param recipients_post_code: 收件人邮编
         :param product_name: 商品名称
         :param addresser_tel: 发货人手机号
         :param recipients_tel: 收件人手机号
         :param sender_name: 发件人姓名
         :param receiver_name: 收件人姓名
         :param weight: 货物重量(kg)
         :param count: 货物数量
         :param amount: 货物单价
         :param currency: 币种
         :param sourceArea: 原产地国别
         :param unit: 货物单位
        '''
        # 1. 获取物流配置
        logistics_data: dict = await self.cache.get(f'logistics')
        if not logistics_data:
            mongo_data: dict = await self.mongo.find_one("LogisticsServiceConfig")
            if not mongo_data:
                return {'code': 500, 'msg': '没有检测到相关配置请联系平台管理员进行配置', 'success': False}
            logistics_data = mongo_data

        # 2. 提取顺丰核心配置
        partner_id = logistics_data.get("partner_id")
        check_word = logistics_data.get("check_word")
        is_production = logistics_data.get("production_environment", False)
        if not partner_id or not check_word:
            return {'code': 500, 'msg': '顺丰配置不完整（partner_id/check_word为必传）', 'success': False}

        # 3. 构造msgData业务报文【完全匹配你提供的示例参数】
        # 字段/值/层级/格式与示例1:1对应，无多余字段
        msg_data = {
            "cargoDetails": [
                {
                    "count": count,
                    "unit": unit,
                    "weight": weight,
                    "amount": amount,
                    "currency": currency,
                    "name": product_name,
                    "sourceArea": sourceArea
                }
            ],
            "contactInfoList": [
                # 发件人：contactType=1，匹配示例字段
                {
                    "address": ship_address,
                    "contact": sender_name,
                    "contactType": 1,
                    "country": "CN",
                    "postCode": addresser_post_code,
                    "tel": addresser_tel
                },
                # 收件人：contactType=2，含company字段（示例独有）
                {
                    "address": shipping_address,
                    "company": "顺丰速运",  # 示例固定值，可根据业务动态传参
                    "contact": receiver_name,
                    "contactType": 2,
                    "country": "CN",
                    "postCode": recipients_post_code,
                    "tel": recipients_tel
                }
            ],
            "language": "zh_CN",  # 示例固定值
            "orderId": order_number  # 传入的业务订单号
        }
        # 转JSON字符串，保留示例的数值精度（不做四舍五入）
        msg_data_str = json.dumps(msg_data, ensure_ascii=False)

        # 4. 构造顺丰公共请求参数（文档必传，解决A1001核心）
        request_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp() * 1000)
        # 数字签名：base64(md5(msgDataStr + checkWord))
        sign_str = f"{msg_data_str}{check_word}"
        md5_obj = hashlib.md5(sign_str.encode("utf-8"))
        msg_digest = base64.b64encode(md5_obj.digest()).decode("utf-8")

        # 5. 构造form表单请求体（文档要求，非JSON）
        form_data = {
            "partnerID": partner_id,
            "requestID": request_id,
            "serviceCode": self.service_code,
            "timestamp": timestamp,
            "msgDigest": msg_digest,
            "msgData": msg_data_str
        }

        # 6. 文档标准请求头
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Python-Httpx/0.27.0"
        }

        # 7. 选择接口环境
        url = self.production if is_production else self.sandbox

        try:
            # 8. 发送POST请求（form表单，自动URL编码）
            async with httpx.AsyncClient(limits=self.limits, timeout=30.0) as client:
                response = await client.post(
                    url=url,
                    headers=headers,
                    data=form_data,
                    follow_redirects=True
                )
            response_data = response.json()
            api_result_code = response_data.get("apiResultCode", "")
            api_error_msg = response_data.get("apiErrorMsg", "接口请求异常")

            # 解析返回结果
            if api_result_code == "A1000":
                api_result_data = response_data.get("apiResultData", {})
                business_success = api_result_data.get("success", False)
                business_msg = api_result_data.get("errorMsg", api_error_msg)
                return {
                    "code": 200 if business_success else 400,
                    "msg": business_msg if business_msg else "下单成功",
                    "success": business_success,
                    "data": api_result_data,
                    "request_id": request_id,
                    "waybill_list": api_result_data.get("msgData", {}).get("waybillNoInfolist", [])
                }
            else:
                return {
                    "code": 400,
                    "msg": f"顺丰接口校验失败：{api_error_msg}（错误码：{api_result_code}）",
                    "success": False,
                    "data": response_data,
                    "request_id": request_id
                }

        except httpx.TimeoutException:
            return {"code": 504, "msg": "顺丰接口请求超时", "success": False, "request_id": request_id}
        except json.JSONDecodeError:
            return {"code": 500, "msg": "顺丰接口返回非JSON格式数据", "success": False, "request_id": request_id}
        except Exception as e:
            return {"code": 500, "msg": f"下单异常：{str(e)}", "success": False, "request_id": request_id}