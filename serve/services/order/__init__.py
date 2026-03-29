"""
订单服务层
- 下单：乐观锁扣减库存 + 幂等性保障
- 支付：调用支付宝 page_execute 生成跳转表单，资金由平台代收
- 异步通知：验签后确认支付，资金进入担保账户
- 超时关闭：先查支付宝确认未支付才关闭，防止"吞钱"
- 确认收货：担保资金按 90/10 分账（卖家 90%，平台 10%）
- 退款：调用支付宝退款 API + 回滚库存
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

ORDER_EXPIRE_MINUTES = 15
PLATFORM_COMMISSION_RATE = Decimal("0.10")


def generate_order_no() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"ORD{ts}{short_uuid}"


def generate_transaction_no() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:10].upper()
    return f"TXN{ts}{short_uuid}"


class OrderService:

    def __init__(self, db_pool, mongodb, redis=None):
        self.db = db_pool
        self.mongo = mongodb
        self.redis = redis

    # ════════════════════ 幂等性 ════════════════════

    async def _check_idempotency(self, key: str, prefix: str) -> str | None:
        if not self.redis:
            return None
        redis_key = f"idempotent:{prefix}:{key}"
        return await self.redis.get(redis_key)

    async def _set_idempotency(self, key: str, prefix: str, value: str, ttl: int = 3600):
        if not self.redis:
            return
        redis_key = f"idempotent:{prefix}:{key}"
        await self.redis.setex(redis_key, ttl, value)

    # ════════════════════ 支付宝交易查询（核心防吞钱） ════════════════════

    async def _query_alipay_trade(self, txn_no: str) -> dict | None:
        """
        调用 alipay.trade.query 查询单笔交易状态。
        返回 {"trade_status": ..., "trade_no": ...} 或 None（查询失败）。
        """
        try:
            from services.pay.mangement_pay import AlipayClient
            from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest

            client = await AlipayClient.from_db(self.mongo)
            request = AlipayTradeQueryRequest()
            request.biz_content = {"out_trade_no": txn_no}
            raw = await client.execute(request)
            await client.close()

            result = json.loads(raw) if isinstance(raw, str) else raw
            code = result.get("code", "")

            if code == "10000":
                return {
                    "trade_status": result.get("trade_status", ""),
                    "trade_no": result.get("trade_no", ""),
                    "total_amount": result.get("total_amount", "0"),
                }
            return None
        except Exception as e:
            logger.warning("查询支付宝交易 %s 失败: %s", txn_no, e)
            return None

    # ════════════════════ 确认到账（公共逻辑，防重） ════════════════════

    async def _confirm_payment(self, order_no: str, txn_no: str, trade_no: str, pay_user: str) -> bool:
        """
        将订单确认为已支付，写入担保账户。
        内置防重：订单已 paid 或 escrow 已存在时安全返回。
        返回 True=本次确认成功 / False=已确认过（幂等）。
        """
        # 更新流水
        await self.db.execute_query(
            """UPDATE payment_transactions SET status = 'success', trade_no = %s, paid_at = NOW()
               WHERE transaction_no = %s AND status = 'pending'""",
            (trade_no, txn_no),
        )

        # 查订单
        order_rows = await self.db.execute_query(
            "SELECT id, mall_id, total_amount, status, version FROM orders WHERE order_no = %s",
            (order_no,),
        )
        if not order_rows:
            logger.error("_confirm_payment: 订单 %s 不存在", order_no)
            return False

        o_id, o_mall, o_amount, o_status, o_version = order_rows[0]

        if o_status == "paid":
            return False

        if o_status != "pending":
            logger.warning("_confirm_payment: 订单 %s 状态为 %s，无法确认", order_no, o_status)
            return False

        # 乐观锁 pending -> paid
        await self.db.execute_query(
            """UPDATE orders SET status = 'paid', paid_at = NOW(), version = version + 1
               WHERE id = %s AND status = 'pending' AND version = %s""",
            (o_id, o_version),
        )

        # 计算平台抽成
        amount = Decimal(str(float(o_amount)))
        commission = (amount * PLATFORM_COMMISSION_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        seller_amt = amount - commission

        # 写入担保账户（防重：先检查是否已存在）
        existing_escrow = await self.db.execute_query(
            "SELECT id FROM escrow_account WHERE order_no = %s", (order_no,)
        )
        if not existing_escrow:
            await self.db.execute_query(
                """INSERT INTO escrow_account
                   (order_no, mall_id, user, amount, platform_rate, platform_commission, seller_amount, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'holding')""",
                (order_no, o_mall, pay_user, float(amount),
                 float(PLATFORM_COMMISSION_RATE), float(commission), float(seller_amt)),
            )

        logger.info("确认支付到账: order=%s txn=%s trade=%s 抽成=%.2f 卖家=%.2f",
                     order_no, txn_no, trade_no, commission, seller_amt)
        return True

    # ════════════════════ 检查订单所有流水是否有已付款的 ════════════════════

    async def _check_all_transactions_paid(self, order_no: str) -> dict | None:
        """
        遍历该订单所有 pending 流水，逐一查询支付宝。
        如果发现任一笔已付款，立即确认到账并返回结果。
        返回 None 表示全部未付款。
        """
        txn_rows = await self.db.execute_query(
            "SELECT transaction_no, user, amount FROM payment_transactions WHERE order_no = %s AND status = 'pending' ORDER BY created_at DESC",
            (order_no,),
        )
        if not txn_rows:
            return None

        for txn_no, pay_user, txn_amount in txn_rows:
            alipay_result = await self._query_alipay_trade(txn_no)
            if not alipay_result:
                continue

            if alipay_result["trade_status"] in ("TRADE_SUCCESS", "TRADE_FINISHED"):
                await self._confirm_payment(order_no, txn_no, alipay_result["trade_no"], pay_user)
                return {
                    "paid": True,
                    "txn_no": txn_no,
                    "trade_no": alipay_result["trade_no"],
                }

        return None

    # ════════════════════ 创建订单 ════════════════════

    async def create_order(self, user: str, items: list, address_id: int,
                           remark: str | None, idempotency_key: str,
                           user_coupon_id: int | None = None) -> dict:
        existing = await self._check_idempotency(idempotency_key, "order")
        if existing:
            return {"success": True, "msg": "订单已创建（幂等）", "order_no": existing}

        addr_rows = await self.db.execute_query(
            "SELECT address_id, name, phone, save, city, county, address FROM user_address WHERE address_id = %s AND user = %s",
            (address_id, user),
        )
        if not addr_rows:
            return {"success": False, "msg": "收货地址不存在"}
        addr = addr_rows[0]
        receiver_name = addr[1]
        receiver_phone = addr[2]
        receiver_addr = f"{addr[3]} {addr[4]} {addr[5]} {addr[6]}"

        order_no = generate_order_no()
        expire_at = datetime.now() + timedelta(minutes=ORDER_EXPIRE_MINUTES)
        total_amount = 0
        order_items_data = []

        mall_ids = set(item.mall_id for item in items)
        if len(mall_ids) != 1:
            return {"success": False, "msg": "一个订单只能包含同一店铺的商品"}
        mall_id = mall_ids.pop()

        for item in items:
            doc = await self.mongo.find_one(
                "shopping",
                {"mall_id": item.mall_id, "shopping_id": item.shopping_id, "audit": 1},
            )
            if not doc:
                return {"success": False, "msg": f"商品 {item.shopping_id} 不存在或已下架"}

            spec_list = doc.get("specification_list") or []
            spec = None
            for s in spec_list:
                if s.get("specification_id") == item.specification_id:
                    spec = s
                    break
            if not spec:
                return {"success": False, "msg": f"商品 {item.shopping_id} 的规格 {item.specification_id} 不存在"}

            price = float(spec.get("price", 0))
            stock = int(spec.get("stock", 0))
            if stock < item.quantity:
                return {"success": False, "msg": f"商品「{doc.get('name', '')}」库存不足，当前仅剩 {stock} 件"}

            max_retry = 3
            deducted = False
            for attempt in range(max_retry):
                await self.db.execute_query(
                    """UPDATE specification
                       SET stock = stock - %s
                       WHERE mall_id = %s AND shopping_id = %s AND specification_id = %s
                         AND stock >= %s""",
                    (item.quantity, item.mall_id, item.shopping_id, item.specification_id, item.quantity),
                )
                verify = await self.db.execute_query(
                    """SELECT stock FROM specification
                       WHERE mall_id = %s AND shopping_id = %s AND specification_id = %s""",
                    (item.mall_id, item.shopping_id, item.specification_id),
                )
                if verify is not None:
                    deducted = True
                    break
                if attempt < max_retry - 1:
                    import asyncio
                    await asyncio.sleep(0.05 * (attempt + 1))

            if not deducted:
                return {"success": False, "msg": f"商品「{doc.get('name', '')}」库存扣减失败，请重试"}

            try:
                await self.mongo.update_one(
                    "shopping",
                    {"mall_id": item.mall_id, "shopping_id": item.shopping_id,
                     "specification_list.specification_id": item.specification_id},
                    {"$inc": {"specification_list.$.stock": -item.quantity}},
                )
            except Exception as e:
                logger.warning("同步 MongoDB 库存快照失败: %s", e)

            subtotal = round(price * item.quantity, 2)
            total_amount += subtotal
            order_items_data.append({
                "mall_id": item.mall_id,
                "shopping_id": item.shopping_id,
                "specification_id": item.specification_id,
                "product_name": doc.get("name", ""),
                "spec_name": spec.get("name", ""),
                "price": price,
                "quantity": item.quantity,
                "subtotal": subtotal,
            })

        total_amount = round(total_amount, 2)

        coupon_discount = 0
        actual_amount = total_amount
        if user_coupon_id:
            from services.promotion import PromotionService
            from services.promotion.strategy import get_coupon_strategy

            promo_svc = PromotionService(self.db)
            uc_rows = await self.db.execute_query(
                """SELECT uc.id, uc.coupon_id, uc.status, c.coupon_type,
                          c.scope, c.min_order_amount, c.discount_value,
                          c.max_discount, c.status AS c_status, c.mall_id,
                          c.start_time, c.end_time
                   FROM user_coupons uc
                   JOIN coupons c ON c.id = uc.coupon_id
                   WHERE uc.id = %s AND uc.user = %s""",
                (user_coupon_id, user),
            )
            if not uc_rows:
                return {"success": False, "msg": "优惠券不存在"}

            uc = uc_rows[0]
            if uc[2] != "unused":
                return {"success": False, "msg": "优惠券已使用或已过期"}
            if uc[8] != "active":
                return {"success": False, "msg": "优惠券已失效"}

            now = datetime.now()
            if now < uc[10] or now > uc[11]:
                return {"success": False, "msg": "优惠券不在有效期内"}

            scope = uc[4]
            coupon_mall = uc[9]
            if scope == "store" and coupon_mall != mall_id:
                return {"success": False, "msg": "该优惠券不适用于此店铺"}
            if scope == "product" and coupon_mall != mall_id:
                return {"success": False, "msg": "该优惠券不适用于此店铺商品"}

            if total_amount < float(uc[5]):
                return {"success": False, "msg": f"订单金额未达到优惠券最低消费 ¥{float(uc[5]):.2f}"}

            strategy = get_coupon_strategy(uc[3])
            coupon_discount = float(strategy.calculate_discount(
                Decimal(str(total_amount)),
                {"min_order_amount": float(uc[5]), "discount_value": float(uc[6]),
                 "max_discount": float(uc[7]) if uc[7] else None},
            ))
            actual_amount = round(total_amount - coupon_discount, 2)
            if actual_amount < 0.01:
                actual_amount = 0.01

        await self.db.execute_query(
            """INSERT INTO orders
               (order_no, user, mall_id, total_amount, status, address_id,
                receiver_name, receiver_phone, receiver_addr, remark, version, expire_at)
               VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s, %s, %s, 0, %s)""",
            (order_no, user, mall_id, actual_amount, address_id,
             receiver_name, receiver_phone, receiver_addr, remark,
             expire_at.strftime("%Y-%m-%d %H:%M:%S")),
        )

        order_row = await self.db.execute_query(
            "SELECT id FROM orders WHERE order_no = %s", (order_no,)
        )
        order_id = order_row[0][0]

        for oi in order_items_data:
            await self.db.execute_query(
                """INSERT INTO order_items
                   (order_id, order_no, mall_id, shopping_id, specification_id,
                    product_name, spec_name, price, quantity, subtotal)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (order_id, order_no, oi["mall_id"], oi["shopping_id"],
                 oi["specification_id"], oi["product_name"], oi["spec_name"],
                 oi["price"], oi["quantity"], oi["subtotal"]),
            )

        if user_coupon_id and coupon_discount > 0:
            from services.promotion import PromotionService
            promo_svc = PromotionService(self.db)
            await promo_svc.use_coupon(user_coupon_id, user, order_no)

        await self._set_idempotency(idempotency_key, "order", order_no, ttl=1800)

        result_data = {
            "success": True,
            "msg": "下单成功",
            "order_no": order_no,
            "total_amount": actual_amount,
            "expire_at": expire_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if coupon_discount > 0:
            result_data["original_amount"] = total_amount
            result_data["coupon_discount"] = coupon_discount
        return result_data

    # ════════════════════ 支付订单（生成支付宝跳转表单） ════════════════════

    async def pay_order(self, user: str, order_no: str, pay_method: str,
                        idempotency_key: str, default_return_url: str = "") -> dict:
        existing = await self._check_idempotency(idempotency_key, "pay")
        if existing:
            return {"success": True, "msg": "支付已处理（幂等）", "transaction_no": existing}

        rows = await self.db.execute_query(
            "SELECT id, order_no, user, mall_id, total_amount, status, version, expire_at FROM orders WHERE order_no = %s",
            (order_no,),
        )
        if not rows:
            return {"success": False, "msg": "订单不存在"}

        o_id, o_no, o_user, o_mall, o_amount, o_status, o_version, o_expire = rows[0]

        if o_user != user:
            return {"success": False, "msg": "无权操作此订单"}
        if o_status == "paid":
            return {"success": True, "msg": "订单已支付，无需重复操作"}
        if o_status != "pending":
            return {"success": False, "msg": f"订单状态为 {o_status}，无法支付"}
        if datetime.now() > o_expire:
            return {"success": False, "msg": "订单已超时，请重新下单"}

        # 复用已有的 pending 流水，避免重复创建多条
        existing_txn = await self.db.execute_query(
            "SELECT transaction_no FROM payment_transactions WHERE order_no = %s AND status = 'pending' ORDER BY created_at DESC LIMIT 1",
            (order_no,),
        )

        if existing_txn:
            txn_no = existing_txn[0][0]
        else:
            txn_no = generate_transaction_no()
            await self.db.execute_query(
                """INSERT INTO payment_transactions
                   (transaction_no, order_no, user, amount, pay_method, status)
                   VALUES (%s, %s, %s, %s, %s, 'pending')""",
                (txn_no, order_no, user, o_amount, pay_method),
            )

        items = await self.db.execute_query(
            "SELECT product_name, quantity FROM order_items WHERE order_no = %s", (order_no,)
        )
        subject = "xb商城订单"
        if items:
            names = [f"{it[0]}x{it[1]}" for it in items[:3]]
            subject = "、".join(names)
            if len(items) > 3:
                subject += " 等"

        try:
            from services.pay.mangement_pay import AlipayClient
            from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest

            client = await AlipayClient.from_db(self.mongo)

            request = AlipayTradePagePayRequest()
            request.biz_content = {
                "out_trade_no": txn_no,
                "total_amount": str(float(o_amount)),
                "subject": subject,
                "product_code": "FAST_INSTANT_TRADE_PAY",
                "timeout_express": f"{ORDER_EXPIRE_MINUTES}m",
            }

            if client._notify_url:
                request.notify_url = client._notify_url
            request.return_url = client._return_url or default_return_url

            pay_form = await client.page_execute(request, http_method="POST")
            await client.close()

        except Exception as e:
            logger.error("调用支付宝下单失败: %s", e, exc_info=True)
            return {"success": False, "msg": f"支付宝下单失败: {str(e)}"}

        await self._set_idempotency(idempotency_key, "pay", txn_no, ttl=1800)

        return {
            "success": True,
            "msg": "支付表单已生成",
            "transaction_no": txn_no,
            "amount": float(o_amount),
            "pay_form": pay_form,
        }

    # ════════════════════ 支付宝异步通知 ════════════════════

    async def handle_alipay_notify(self, params: dict) -> str:
        trade_status = params.get("trade_status", "")
        out_trade_no = params.get("out_trade_no", "")
        trade_no = params.get("trade_no", "")
        total_amount_str = params.get("total_amount", "0")

        if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            return "success"

        txn_rows = await self.db.execute_query(
            "SELECT transaction_no, order_no, user, amount, status FROM payment_transactions WHERE transaction_no = %s",
            (out_trade_no,),
        )
        if not txn_rows:
            logger.warning("支付宝通知: 流水号 %s 不存在", out_trade_no)
            return "fail"

        txn_no, order_no, pay_user, txn_amount, txn_status = txn_rows[0]

        if txn_status == "success":
            return "success"

        if abs(float(txn_amount) - float(total_amount_str)) > 0.01:
            logger.error("支付宝通知金额不匹配: 流水=%s 通知=%s", txn_amount, total_amount_str)
            return "fail"

        await self._confirm_payment(order_no, txn_no, trade_no, pay_user)
        return "success"

    # ════════════════════ 主动查询支付宝交易状态 ════════════════════

    async def sync_payment_status(self, order_no: str) -> dict:
        """
        遍历该订单所有 pending 流水，逐一查询支付宝。
        发现已付款则确认到账。
        """
        # 先检查订单是否已经是 paid
        order_rows = await self.db.execute_query(
            "SELECT status FROM orders WHERE order_no = %s", (order_no,)
        )
        if order_rows and order_rows[0][0] == "paid":
            return {"success": True, "msg": "订单已支付", "already_paid": True}

        if order_rows and order_rows[0][0] != "pending":
            return {"success": False, "msg": f"订单状态为 {order_rows[0][0]}"}

        result = await self._check_all_transactions_paid(order_no)

        if result and result.get("paid"):
            return {"success": True, "msg": "支付确认成功", "already_paid": False}

        return {"success": False, "msg": "支付宝尚未确认到账，请稍后再试"}

    # ════════════════════ 取消订单（先查支付宝） ════════════════════

    async def cancel_order(self, user: str, order_no: str) -> dict:
        rows = await self.db.execute_query(
            "SELECT id, user, status, version FROM orders WHERE order_no = %s", (order_no,),
        )
        if not rows:
            return {"success": False, "msg": "订单不存在"}

        o_id, o_user, o_status, o_version = rows[0]
        if o_user != user:
            return {"success": False, "msg": "无权操作此订单"}
        if o_status != "pending":
            return {"success": False, "msg": f"订单状态为 {o_status}，无法取消"}

        # 取消前先查支付宝，如果用户其实已经付款了就不能取消
        paid_check = await self._check_all_transactions_paid(order_no)
        if paid_check and paid_check.get("paid"):
            return {"success": False, "msg": "该订单已在支付宝完成付款，无法取消。请刷新页面查看最新状态。"}

        await self.db.execute_query(
            """UPDATE orders SET status = 'closed', closed_at = NOW(), version = version + 1
               WHERE id = %s AND status = 'pending' AND version = %s""",
            (o_id, o_version),
        )

        await self.db.execute_query(
            "UPDATE payment_transactions SET status = 'failed' WHERE order_no = %s AND status = 'pending'",
            (order_no,),
        )

        await self._rollback_stock(order_no)
        return {"success": True, "msg": "订单已取消"}

    # ════════════════════ 定时关闭超时订单（先查支付宝） ════════════════════

    async def close_expired_orders(self) -> int:
        expired = await self.db.execute_query(
            "SELECT id, order_no, version FROM orders WHERE status = 'pending' AND expire_at < NOW()"
        )
        if not expired:
            return 0

        closed_count = 0
        for o_id, o_no, o_version in expired:
            try:
                # 关闭前先查支付宝，如果已付款就确认而不是关闭
                paid_check = await self._check_all_transactions_paid(o_no)
                if paid_check and paid_check.get("paid"):
                    logger.info("超时订单 %s 实际已付款，已自动确认到账（防吞钱）", o_no)
                    continue

                await self.db.execute_query(
                    """UPDATE orders SET status = 'closed', closed_at = NOW(), version = version + 1
                       WHERE id = %s AND status = 'pending' AND version = %s""",
                    (o_id, o_version),
                )
                await self.db.execute_query(
                    "UPDATE payment_transactions SET status = 'failed' WHERE order_no = %s AND status = 'pending'",
                    (o_no,),
                )
                await self._rollback_stock(o_no)
                closed_count += 1
                logger.info("超时关闭订单: %s", o_no)
            except Exception as e:
                logger.error("关闭超时订单 %s 失败: %s", o_no, e)

        return closed_count

    # ════════════════════ 确认收货（90/10 分账） ════════════════════

    async def confirm_receive(self, user: str, order_no: str) -> dict:
        rows = await self.db.execute_query(
            "SELECT id, user, mall_id, total_amount, status, version FROM orders WHERE order_no = %s",
            (order_no,),
        )
        if not rows:
            return {"success": False, "msg": "订单不存在"}

        o_id, o_user, o_mall, o_amount, o_status, o_version = rows[0]
        if o_user != user:
            return {"success": False, "msg": "无权操作此订单"}
        if o_status not in ("paid", "shipped"):
            return {"success": False, "msg": f"订单状态为 {o_status}，无法确认收货"}

        await self.db.execute_query(
            """UPDATE orders SET status = 'received', received_at = NOW(), version = version + 1
               WHERE id = %s AND status = %s AND version = %s""",
            (o_id, o_status, o_version),
        )

        await self.db.execute_query(
            """UPDATE escrow_account SET status = 'released', released_at = NOW()
               WHERE order_no = %s AND status = 'holding'""",
            (order_no,),
        )

        esc = await self.db.execute_query(
            "SELECT amount, platform_commission, seller_amount FROM escrow_account WHERE order_no = %s",
            (order_no,),
        )
        detail = {}
        if esc:
            detail = {
                "total_amount": float(esc[0][0]),
                "platform_commission": float(esc[0][1]),
                "seller_amount": float(esc[0][2]),
            }

        return {
            "success": True,
            "msg": f"确认收货成功，卖家实收 ¥{detail.get('seller_amount', 0):.2f}，平台服务费 ¥{detail.get('platform_commission', 0):.2f}",
            **detail,
        }

    # ════════════════════ 退款（支付宝退款 API） ════════════════════

    async def refund_order(self, user: str, order_no: str, reason: str | None) -> dict:
        rows = await self.db.execute_query(
            "SELECT id, user, mall_id, total_amount, status, version FROM orders WHERE order_no = %s",
            (order_no,),
        )
        if not rows:
            return {"success": False, "msg": "订单不存在"}

        o_id, o_user, o_mall, o_amount, o_status, o_version = rows[0]
        if o_user != user:
            return {"success": False, "msg": "无权操作此订单"}
        if o_status not in ("paid", "shipped"):
            return {"success": False, "msg": f"订单状态为 {o_status}，无法退款"}

        txn_rows = await self.db.execute_query(
            "SELECT transaction_no, trade_no, amount FROM payment_transactions WHERE order_no = %s AND status = 'success' LIMIT 1",
            (order_no,),
        )
        if not txn_rows:
            return {"success": False, "msg": "未找到支付记录"}

        txn_no, trade_no, refund_amount = txn_rows[0]

        try:
            from services.pay.mangement_pay import AlipayClient
            from alipay.aop.api.request.AlipayTradeRefundRequest import AlipayTradeRefundRequest

            client = await AlipayClient.from_db(self.mongo)

            request = AlipayTradeRefundRequest()
            request.biz_content = {
                "out_trade_no": txn_no,
                "trade_no": trade_no or "",
                "refund_amount": str(float(refund_amount)),
                "refund_reason": reason or "买家申请退款",
                "out_request_no": f"REFUND_{txn_no}",
            }

            raw = await client.execute(request)
            await client.close()

            result = json.loads(raw) if isinstance(raw, str) else raw
            code = result.get("code", "")

            if code != "10000":
                sub_msg = result.get("sub_msg", result.get("msg", "未知错误"))
                logger.error("支付宝退款失败: %s", result)
                return {"success": False, "msg": f"支付宝退款失败: {sub_msg}"}

        except Exception as e:
            logger.error("调用支付宝退款异常: %s", e, exc_info=True)
            return {"success": False, "msg": f"退款请求失败: {str(e)}"}

        await self.db.execute_query(
            """UPDATE orders SET status = 'refunded', closed_at = NOW(), version = version + 1
               WHERE id = %s AND status = %s AND version = %s""",
            (o_id, o_status, o_version),
        )

        await self.db.execute_query(
            """UPDATE escrow_account SET status = 'refunded', released_at = NOW()
               WHERE order_no = %s AND status = 'holding'""",
            (order_no,),
        )

        await self.db.execute_query(
            """UPDATE payment_transactions SET status = 'refunded', refunded_at = NOW()
               WHERE order_no = %s AND status = 'success'""",
            (order_no,),
        )

        await self._rollback_stock(order_no)
        return {"success": True, "msg": "退款成功，资金将原路退回"}

    async def _latest_refunds_for_orders(self, order_nos: list[str]) -> dict[str, dict]:
        """每个订单最新一条退款申请（用于买家端展示：卖家拒绝后应引导平台介入）。"""
        if not order_nos:
            return {}
        placeholders = ",".join(["%s"] * len(order_nos))
        sql = f"""
            SELECT r.order_no, r.refund_no, r.status, r.seller_remark
            FROM refund_requests r
            INNER JOIN (
                SELECT order_no, MAX(id) AS mid
                FROM refund_requests
                WHERE order_no IN ({placeholders})
                GROUP BY order_no
            ) x ON r.order_no = x.order_no AND r.id = x.mid
        """
        rows = await self.db.execute_query(sql, tuple(order_nos))
        out: dict[str, dict] = {}
        for row in rows or []:
            out[row[0]] = {
                "refund_no": row[1],
                "status": row[2],
                "seller_remark": row[3],
            }
        return out

    # ════════════════════ 查询订单列表 ════════════════════

    async def get_order_list(self, user: str, status: str | None,
                            page: int, page_size: int,
                            keyword: str | None = None) -> dict:
        offset = (page - 1) * page_size
        where = "WHERE o.user = %s"
        params: list = [user]

        if status:
            where += " AND o.status = %s"
            params.append(status)

        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            where += """ AND (o.order_no LIKE %s
                          OR o.receiver_name LIKE %s
                          OR EXISTS (SELECT 1 FROM order_items oi
                                     WHERE oi.order_no = o.order_no
                                       AND oi.product_name LIKE %s))"""
            params.extend([kw, kw, kw])

        count_row = await self.db.execute_query(
            f"SELECT COUNT(*) FROM orders o {where}", tuple(params),
        )
        total = count_row[0][0] if count_row else 0

        rows = await self.db.execute_query(
            f"""SELECT o.id, o.order_no, o.mall_id, o.total_amount, o.status,
                       o.receiver_name, o.receiver_addr, o.remark,
                       o.expire_at, o.paid_at, o.created_at
                FROM orders o {where}
                ORDER BY o.created_at DESC
                LIMIT %s OFFSET %s""",
            tuple(params + [page_size, offset]),
        )

        order_nos = [r[1] for r in (rows or [])]
        refund_map = await self._latest_refunds_for_orders(order_nos)

        orders = []
        for r in (rows or []):
            order_no = r[1]
            order_data = {
                "id": r[0], "order_no": order_no, "mall_id": r[2],
                "total_amount": float(r[3]), "status": r[4],
                "receiver_name": r[5], "receiver_addr": r[6],
                "remark": r[7],
                "expire_at": str(r[8]) if r[8] else None,
                "paid_at": str(r[9]) if r[9] else None,
                "created_at": str(r[10]) if r[10] else None,
                "latest_refund": refund_map.get(order_no),
            }
            items = await self.db.execute_query(
                """SELECT product_name, spec_name, price, quantity, subtotal,
                          shopping_id, mall_id
                   FROM order_items WHERE order_no = %s""",
                (order_no,),
            )
            order_data["items"] = [
                {
                    "product_name": it[0], "spec_name": it[1],
                    "price": float(it[2]), "quantity": it[3],
                    "subtotal": float(it[4]),
                    "shopping_id": it[5], "mall_id": it[6],
                }
                for it in (items or [])
            ]
            orders.append(order_data)

        return {
            "success": True, "total": total,
            "page": page, "page_size": page_size,
            "list": orders,
        }

    # ════════════════════ 查询订单详情 ════════════════════

    async def get_order_detail(self, user: str, order_no: str) -> dict:
        rows = await self.db.execute_query(
            """SELECT id, order_no, mall_id, total_amount, status,
                      receiver_name, receiver_phone, receiver_addr, remark,
                      expire_at, paid_at, shipped_at, received_at, closed_at, created_at
               FROM orders WHERE order_no = %s AND user = %s""",
            (order_no, user),
        )
        if not rows:
            return {"success": False, "msg": "订单不存在"}

        r = rows[0]
        detail = {
            "id": r[0], "order_no": r[1], "mall_id": r[2],
            "total_amount": float(r[3]), "status": r[4],
            "receiver_name": r[5], "receiver_phone": r[6],
            "receiver_addr": r[7], "remark": r[8],
            "expire_at": str(r[9]) if r[9] else None,
            "paid_at": str(r[10]) if r[10] else None,
            "shipped_at": str(r[11]) if r[11] else None,
            "received_at": str(r[12]) if r[12] else None,
            "closed_at": str(r[13]) if r[13] else None,
            "created_at": str(r[14]) if r[14] else None,
        }

        items = await self.db.execute_query(
            """SELECT product_name, spec_name, price, quantity, subtotal,
                      shopping_id, mall_id, specification_id
               FROM order_items WHERE order_no = %s""",
            (order_no,),
        )
        detail["items"] = [
            {
                "product_name": it[0], "spec_name": it[1],
                "price": float(it[2]), "quantity": it[3],
                "subtotal": float(it[4]),
                "shopping_id": it[5], "mall_id": it[6],
                "specification_id": it[7],
            }
            for it in (items or [])
        ]

        txn_rows = await self.db.execute_query(
            """SELECT transaction_no, amount, pay_method, status, trade_no, paid_at
               FROM payment_transactions WHERE order_no = %s ORDER BY created_at DESC""",
            (order_no,),
        )
        detail["transactions"] = [
            {
                "transaction_no": t[0], "amount": float(t[1]),
                "pay_method": t[2], "status": t[3],
                "trade_no": t[4],
                "paid_at": str(t[5]) if t[5] else None,
            }
            for t in (txn_rows or [])
        ]

        esc_rows = await self.db.execute_query(
            """SELECT amount, platform_rate, platform_commission, seller_amount, status, released_at
               FROM escrow_account WHERE order_no = %s""",
            (order_no,),
        )
        if esc_rows:
            e = esc_rows[0]
            detail["escrow"] = {
                "amount": float(e[0]),
                "platform_rate": f"{float(e[1]) * 100:.0f}%",
                "platform_commission": float(e[2]),
                "seller_amount": float(e[3]),
                "status": e[4],
                "released_at": str(e[5]) if e[5] else None,
            }

        return {"success": True, "data": detail}

    # ════════════════════ 库存回滚 ════════════════════

    async def _rollback_stock(self, order_no: str):
        items = await self.db.execute_query(
            "SELECT mall_id, shopping_id, specification_id, quantity FROM order_items WHERE order_no = %s",
            (order_no,),
        )
        if not items:
            return

        for mall_id, shopping_id, spec_id, qty in items:
            try:
                await self.db.execute_query(
                    """UPDATE specification SET stock = stock + %s
                       WHERE mall_id = %s AND shopping_id = %s AND specification_id = %s""",
                    (qty, mall_id, shopping_id, spec_id),
                )
                await self.mongo.update_one(
                    "shopping",
                    {"mall_id": mall_id, "shopping_id": shopping_id,
                     "specification_list.specification_id": spec_id},
                    {"$inc": {"specification_list.$.stock": qty}},
                )
            except Exception as e:
                logger.error("回滚库存失败 mall_id=%s shopping_id=%s spec_id=%s: %s",
                             mall_id, shopping_id, spec_id, e)
