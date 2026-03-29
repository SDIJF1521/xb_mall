"""
订单模块路由
- POST   /order/create            创建订单（幂等）
- POST   /order/pay               发起支付（返回支付宝跳转表单）
- POST   /order/cancel            取消订单
- POST   /order/confirm           确认收货（释放担保资金，90% 卖家 / 10% 平台）
- POST   /order/refund            申请退款（调用支付宝退款 API）
- GET    /order/list               订单列表
- GET    /order/detail             订单详情
- POST   /order/alipay_notify     支付宝异步通知回调
- GET    /order/alipay_return     支付宝同步跳转
"""

import json
import logging
from typing import Annotated
from urllib.parse import parse_qs

from fastapi import APIRouter, Body, Depends, Header, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse

from services.user_info import UserInfo
from services.order import OrderService
from data.data_mods import (
    OrderCreateBody, OrderPayBody, OrderCancelBody,
    OrderConfirmReceiveBody, OrderRefundBody,
    OrderListQuery, OrderDetailQuery,
)
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


def _verify_alipay_sign(pub_key_b64: str, sign_content: str, sign_b64: str, sign_type: str = "RSA2") -> bool:
    """
    验证支付宝回调签名。
    sign_type=RSA2 使用 SHA256，sign_type=RSA 使用 SHA1。
    """
    import base64
    import textwrap
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    try:
        wrapped = "\n".join(textwrap.wrap(pub_key_b64, 64))
        pem = f"-----BEGIN PUBLIC KEY-----\n{wrapped}\n-----END PUBLIC KEY-----\n".encode()
        public_key = serialization.load_pem_public_key(pem)

        signature = base64.b64decode(sign_b64)
        hash_alg = hashes.SHA256() if sign_type == "RSA2" else hashes.SHA1()
        public_key.verify(signature, sign_content.encode("utf-8"), padding.PKCS1v15(), hash_alg)
        return True
    except Exception as e:
        logger.debug("验签异常: %s", e)
        return False


async def _resolve_user(access_token: str) -> str | None:
    user_info = UserInfo(access_token)
    token_data = await user_info.token_analysis()
    if token_data.get("current"):
        return token_data["user"]
    return None


def _get_order_service(redis: RedisClient, mongodb: MongoDBClient) -> OrderService:
    return OrderService(db_pool, mongodb, redis)


# ──────────────────── 创建订单 ────────────────────

@router.post("/order/create")
async def create_order(
    data: Annotated[OrderCreateBody, Body()],
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    try:
        svc = _get_order_service(redis, mongodb)
        result = await svc.create_order(
            user=user, items=data.items, address_id=data.address_id,
            remark=data.remark, idempotency_key=data.idempotency_key,
            user_coupon_id=data.user_coupon_id,
            prefer_mode=data.prefer_mode or "activity",
        )
        return {"code": 200 if result["success"] else 400, **result}
    except Exception as e:
        logger.error("创建订单异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


# ──────────────────── 发起支付（生成支付宝表单） ────────────────────

@router.post("/order/pay")
async def pay_order(
    request: Request,
    data: Annotated[OrderPayBody, Body()],
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    base = str(request.base_url).rstrip("/")
    default_return_url = f"{base}/api/order/alipay_return"

    try:
        svc = _get_order_service(redis, mongodb)
        result = await svc.pay_order(
            user=user, order_no=data.order_no,
            pay_method=data.pay_method, idempotency_key=data.idempotency_key,
            default_return_url=default_return_url,
        )
        return {"code": 200 if result["success"] else 400, **result}
    except Exception as e:
        logger.error("支付订单异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


# ──────────────────── 支付宝异步通知 ────────────────────

@router.post("/order/alipay_notify")
async def alipay_notify(
    request: Request,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """
    支付宝服务端异步通知。
    1. 解析表单参数
    2. 用平台公钥验签
    3. 交给 OrderService.handle_alipay_notify 处理
    """
    try:
        body = await request.body()
        params: dict[str, str] = {}
        for k, v_list in parse_qs(body.decode("utf-8")).items():
            params[k] = v_list[0] if v_list else ""

        # 验签
        sign = params.pop("sign", "")
        sign_type = params.pop("sign_type", "RSA2")

        if sign:
            from alipay.aop.api.util.SignatureUtils import get_sign_content
            from services.pay.mangement_pay import AlipayClient

            client = await AlipayClient.from_db(mongodb)
            sign_content = get_sign_content(params)
            await client.close()

            verified = _verify_alipay_sign(
                client._config.alipay_public_key, sign_content, sign, sign_type,
            )

            if not verified:
                logger.warning("支付宝异步通知验签失败")
                return PlainTextResponse("fail")

        svc = _get_order_service(redis, mongodb)
        resp = await svc.handle_alipay_notify(params)
        return PlainTextResponse(resp)

    except Exception as e:
        logger.error("处理支付宝通知异常: %s", e, exc_info=True)
        return PlainTextResponse("fail")


# ──────────────────── 支付宝同步跳转 ────────────────────

@router.get("/order/alipay_return")
async def alipay_return(
    request: Request,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """
    支付宝付款后浏览器同步跳转回来。
    主动查询支付宝确认支付结果，然后重定向到前端订单页。
    """
    params = dict(request.query_params)
    out_trade_no = params.get("out_trade_no", "")

    if out_trade_no:
        try:
            # 通过流水号找到 order_no
            svc = _get_order_service(redis, mongodb)
            txn_rows = await svc.db.execute_query(
                "SELECT order_no FROM payment_transactions WHERE transaction_no = %s",
                (out_trade_no,),
            )
            if txn_rows:
                order_no = txn_rows[0][0]
                result = await svc.sync_payment_status(order_no)
                logger.info("alipay_return 同步支付结果: %s", result)
        except Exception as e:
            logger.error("alipay_return 同步支付异常: %s", e, exc_info=True)

    return RedirectResponse(url="http://localhost:5173/personal_center?tab=orders", status_code=302)


# ──────────────────── 主动查询支付状态 ────────────────────

@router.post("/order/sync_pay")
async def sync_pay(
    data: dict = Body(...),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    """
    前端主动查询支付状态接口。
    当 notify_url 不可达时（本地开发），前端可调此接口同步支付宝结果。
    """
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    order_no = data.get("order_no", "")
    if not order_no:
        return {"code": 400, "msg": "缺少 order_no", "success": False}

    try:
        svc = _get_order_service(redis, mongodb)
        # 校验订单归属
        rows = await svc.db.execute_query(
            "SELECT user FROM orders WHERE order_no = %s", (order_no,)
        )
        if not rows or rows[0][0] != user:
            return {"code": 403, "msg": "无权操作此订单", "success": False}

        result = await svc.sync_payment_status(order_no)
        return {"code": 200 if result["success"] else 400, **result}
    except Exception as e:
        logger.error("同步支付状态异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


# ──────────────────── 取消订单 ────────────────────

@router.post("/order/cancel")
async def cancel_order(
    data: Annotated[OrderCancelBody, Body()],
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    try:
        svc = _get_order_service(redis, mongodb)
        result = await svc.cancel_order(user=user, order_no=data.order_no)
        return {"code": 200 if result["success"] else 400, **result}
    except Exception as e:
        logger.error("取消订单异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


# ──────────────────── 确认收货 ────────────────────

@router.post("/order/confirm")
async def confirm_receive(
    data: Annotated[OrderConfirmReceiveBody, Body()],
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    try:
        svc = _get_order_service(redis, mongodb)
        result = await svc.confirm_receive(user=user, order_no=data.order_no)
        return {"code": 200 if result["success"] else 400, **result}
    except Exception as e:
        logger.error("确认收货异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


# ──────────────────── 退款 ────────────────────

@router.post("/order/refund")
async def refund_order(
    data: Annotated[OrderRefundBody, Body()],
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    try:
        svc = _get_order_service(redis, mongodb)
        result = await svc.refund_order(user=user, order_no=data.order_no, reason=data.reason)
        return {"code": 200 if result["success"] else 400, **result}
    except Exception as e:
        logger.error("退款异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


# ──────────────────── 订单列表 ────────────────────

@router.get("/order/list")
async def order_list(
    query: OrderListQuery = Depends(),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    try:
        svc = _get_order_service(redis, mongodb)
        result = await svc.get_order_list(
            user=user, status=query.status, page=query.page,
            page_size=query.page_size, keyword=query.keyword,
        )
        return {"code": 200, **result}
    except Exception as e:
        logger.error("查询订单列表异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}


# ──────────────────── 订单详情 ────────────────────

@router.get("/order/detail")
async def order_detail(
    query: OrderDetailQuery = Depends(),
    access_token: Annotated[str | None, Header(alias="access-token")] = None,
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
):
    if not access_token:
        return {"code": 401, "msg": "请先登录", "success": False}
    user = await _resolve_user(access_token)
    if not user:
        return {"code": 403, "msg": "无效的token", "success": False}

    try:
        svc = _get_order_service(redis, mongodb)
        result = await svc.get_order_detail(user=user, order_no=query.order_no)
        return {"code": 200 if result["success"] else 404, **result}
    except Exception as e:
        logger.error("查询订单详情异常: %s", e, exc_info=True)
        return {"code": 500, "msg": f"服务器内部错误: {str(e)}", "success": False}
