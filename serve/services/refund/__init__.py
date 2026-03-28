"""
退款服务层
- 买家申请退款 → 卖家审核 → 同意则执行支付宝退款 / 拒绝则买家可发起纠纷
- 平台介入仲裁 → 判买家胜执行退款 / 判卖家胜关闭纠纷
"""

import json
import uuid
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


def generate_refund_no() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"RFD{ts}{short_uuid}"


class RefundService:

    def __init__(self, db_pool, mongodb, redis=None):
        self.db = db_pool
        self.mongo = mongodb
        self.redis = redis

    # ════════════════════ 买家申请退款 ════════════════════

    async def apply_refund(self, user: str, order_no: str, reason: str | None) -> dict:
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
            return {"success": False, "msg": f"订单状态为 {o_status}，无法申请退款"}

        existing = await self.db.execute_query(
            "SELECT id, status FROM refund_requests WHERE order_no = %s AND status NOT IN ('platform_rejected','refunded') ORDER BY id DESC LIMIT 1",
            (order_no,),
        )
        if existing:
            return {"success": False, "msg": "该订单已有进行中的退款申请"}

        refund_no = generate_refund_no()

        await self.db.execute_query(
            """INSERT INTO refund_requests (refund_no, order_no, mall_id, user, amount, reason, status)
               VALUES (%s, %s, %s, %s, %s, %s, 'pending')""",
            (refund_no, order_no, o_mall, user, float(o_amount), reason),
        )

        await self.db.execute_query(
            """UPDATE orders SET status = 'refund_pending', version = version + 1
               WHERE id = %s AND status = %s AND version = %s""",
            (o_id, o_status, o_version),
        )

        logger.info("退款申请创建: refund=%s order=%s user=%s amount=%s", refund_no, order_no, user, o_amount)
        return {"success": True, "msg": "退款申请已提交，等待卖家审核", "refund_no": refund_no}

    # ════════════════════ 卖家审核退款 ════════════════════

    async def seller_review(self, mall_id: int, refund_no: str, action: str, remark: str | None) -> dict:
        rows = await self.db.execute_query(
            "SELECT id, order_no, mall_id, user, amount, status FROM refund_requests WHERE refund_no = %s",
            (refund_no,),
        )
        if not rows:
            return {"success": False, "msg": "退款单不存在"}

        r_id, order_no, r_mall, r_user, r_amount, r_status = rows[0]
        if r_mall != mall_id:
            return {"success": False, "msg": "无权操作此退款单"}
        if r_status != "pending":
            return {"success": False, "msg": f"退款单状态为 {r_status}，无法审核"}

        if action == "approve":
            await self.db.execute_query(
                """UPDATE refund_requests SET status = 'approved', seller_remark = %s, reviewed_at = NOW()
                   WHERE id = %s""",
                (remark, r_id),
            )
            result = await self._execute_refund(refund_no)
            return result
        else:
            await self.db.execute_query(
                """UPDATE refund_requests SET status = 'rejected', seller_remark = %s, reviewed_at = NOW()
                   WHERE id = %s""",
                (remark, r_id),
            )
            await self.db.execute_query(
                """UPDATE orders SET status = 'paid', version = version + 1
                   WHERE order_no = %s AND status = 'refund_pending'""",
                (order_no,),
            )
            logger.info("卖家拒绝退款: refund=%s order=%s", refund_no, order_no)
            return {"success": True, "msg": "已拒绝退款申请"}

    # ════════════════════ 买家发起纠纷 ════════════════════

    async def buyer_dispute(self, user: str, refund_no: str) -> dict:
        rows = await self.db.execute_query(
            "SELECT id, order_no, user, status FROM refund_requests WHERE refund_no = %s",
            (refund_no,),
        )
        if not rows:
            return {"success": False, "msg": "退款单不存在"}

        r_id, order_no, r_user, r_status = rows[0]
        if r_user != user:
            return {"success": False, "msg": "无权操作"}
        if r_status != "rejected":
            return {"success": False, "msg": "只有被卖家拒绝的退款单才能申请平台介入"}

        await self.db.execute_query(
            "UPDATE refund_requests SET status = 'dispute' WHERE id = %s",
            (r_id,),
        )
        await self.db.execute_query(
            """UPDATE orders SET status = 'refund_pending', version = version + 1
               WHERE order_no = %s""",
            (order_no,),
        )
        logger.info("买家发起纠纷: refund=%s order=%s", refund_no, order_no)
        return {"success": True, "msg": "已申请平台介入，请等待平台处理"}

    # ════════════════════ 平台仲裁 ════════════════════

    async def platform_resolve(self, admin: str, refund_no: str, action: str, remark: str | None) -> dict:
        rows = await self.db.execute_query(
            "SELECT id, order_no, user, amount, status FROM refund_requests WHERE refund_no = %s",
            (refund_no,),
        )
        if not rows:
            return {"success": False, "msg": "退款单不存在"}

        r_id, order_no, r_user, r_amount, r_status = rows[0]
        if r_status != "dispute":
            return {"success": False, "msg": f"退款单状态为 {r_status}，无法仲裁"}

        if action == "approve":
            await self.db.execute_query(
                """UPDATE refund_requests SET status = 'platform_approved',
                   platform_remark = %s, platform_admin = %s, resolved_at = NOW()
                   WHERE id = %s""",
                (remark, admin, r_id),
            )
            result = await self._execute_refund(refund_no)
            return result
        else:
            await self.db.execute_query(
                """UPDATE refund_requests SET status = 'platform_rejected',
                   platform_remark = %s, platform_admin = %s, resolved_at = NOW()
                   WHERE id = %s""",
                (remark, admin, r_id),
            )
            await self.db.execute_query(
                """UPDATE orders SET status = 'paid', version = version + 1
                   WHERE order_no = %s AND status = 'refund_pending'""",
                (order_no,),
            )
            logger.info("平台判卖家胜: refund=%s order=%s admin=%s", refund_no, order_no, admin)
            return {"success": True, "msg": "纠纷已关闭，判定卖家胜"}

    # ════════════════════ 执行支付宝退款 ════════════════════

    async def _execute_refund(self, refund_no: str) -> dict:
        rows = await self.db.execute_query(
            "SELECT id, order_no, user, amount FROM refund_requests WHERE refund_no = %s",
            (refund_no,),
        )
        if not rows:
            return {"success": False, "msg": "退款单不存在"}

        r_id, order_no, r_user, r_amount = rows[0]

        txn_rows = await self.db.execute_query(
            "SELECT transaction_no, trade_no, amount FROM payment_transactions WHERE order_no = %s AND status = 'success' LIMIT 1",
            (order_no,),
        )
        if not txn_rows:
            return {"success": False, "msg": "未找到支付记录，无法退款"}

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
                "refund_reason": "退款审核通过",
                "out_request_no": f"REFUND_{refund_no}",
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
               WHERE order_no = %s AND status IN ('paid','shipped','refund_pending')""",
            (order_no,),
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
        await self.db.execute_query(
            "UPDATE refund_requests SET status = 'refunded', resolved_at = NOW() WHERE refund_no = %s",
            (refund_no,),
        )
        await self._rollback_stock(order_no)

        logger.info("退款执行成功: refund=%s order=%s amount=%s", refund_no, order_no, refund_amount)
        return {"success": True, "msg": "退款成功，资金将原路退回"}

    async def _rollback_stock(self, order_no: str):
        items = await self.db.execute_query(
            "SELECT mall_id, shopping_id, specification_id, quantity FROM order_items WHERE order_no = %s",
            (order_no,),
        )
        if not items:
            return
        for mall_id, shopping_id, spec_id, qty in items:
            doc = await self.mongo.find_one("shopping", {"mall_id": mall_id, "shopping_id": shopping_id})
            if not doc:
                continue
            spec_list = doc.get("specification_list") or []
            for spec in spec_list:
                if spec.get("specification_id") == spec_id:
                    spec["stock"] = int(spec.get("stock", 0)) + qty
                    break
            await self.mongo.update_one(
                "shopping",
                {"mall_id": mall_id, "shopping_id": shopping_id},
                {"$set": {"specification_list": spec_list}},
            )

    # ════════════════════ 查询 ════════════════════

    async def get_refund_detail(self, refund_no: str) -> dict:
        rows = await self.db.execute_query(
            """SELECT r.refund_no, r.order_no, r.mall_id, r.user, r.amount, r.reason,
                      r.status, r.seller_remark, r.platform_remark, r.platform_admin,
                      r.created_at, r.reviewed_at, r.resolved_at
               FROM refund_requests r WHERE r.refund_no = %s""",
            (refund_no,),
        )
        if not rows:
            return {"success": False, "msg": "退款单不存在"}
        r = rows[0]
        return {
            "success": True,
            "data": {
                "refund_no": r[0], "order_no": r[1], "mall_id": r[2], "user": r[3],
                "amount": float(r[4]), "reason": r[5], "status": r[6],
                "seller_remark": r[7], "platform_remark": r[8], "platform_admin": r[9],
                "created_at": r[10].isoformat() if r[10] else None,
                "reviewed_at": r[11].isoformat() if r[11] else None,
                "resolved_at": r[12].isoformat() if r[12] else None,
            },
        }

    async def get_refund_by_order(self, order_no: str) -> dict | None:
        rows = await self.db.execute_query(
            """SELECT refund_no, status, reason, seller_remark, platform_remark, created_at
               FROM refund_requests WHERE order_no = %s
               ORDER BY id DESC LIMIT 1""",
            (order_no,),
        )
        if not rows:
            return None
        r = rows[0]
        return {
            "refund_no": r[0], "status": r[1], "reason": r[2],
            "seller_remark": r[3], "platform_remark": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
        }

    async def get_refund_list_for_seller(self, mall_id: int, status: str | None,
                                          keyword: str | None, page: int, page_size: int) -> dict:
        offset = (page - 1) * page_size
        conditions = ["r.mall_id = %s"]
        params: list = [mall_id]

        if status:
            conditions.append("r.status = %s")
            params.append(status)
        if keyword:
            conditions.append("(r.refund_no LIKE %s OR r.order_no LIKE %s)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        where = " AND ".join(conditions)

        count_rows = await self.db.execute_query(
            f"SELECT COUNT(*) FROM refund_requests r WHERE {where}", tuple(params)
        )
        total = int(count_rows[0][0]) if count_rows else 0

        params.extend([page_size, offset])
        rows = await self.db.execute_query(
            f"""SELECT r.refund_no, r.order_no, r.user, r.amount, r.reason, r.status,
                       r.seller_remark, r.created_at, r.reviewed_at
                FROM refund_requests r WHERE {where}
                ORDER BY r.id DESC LIMIT %s OFFSET %s""",
            tuple(params),
        )

        items = []
        for r in (rows or []):
            items.append({
                "refund_no": r[0], "order_no": r[1], "user": r[2],
                "amount": float(r[3]), "reason": r[4], "status": r[5],
                "seller_remark": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
                "reviewed_at": r[8].isoformat() if r[8] else None,
            })

        return {"success": True, "data": items, "total": total, "page": page, "page_size": page_size}

    async def get_refund_list_for_platform(self, status: str | None,
                                            keyword: str | None, page: int, page_size: int) -> dict:
        offset = (page - 1) * page_size
        conditions = ["1=1"]
        params: list = []

        if status:
            conditions.append("r.status = %s")
            params.append(status)
        else:
            conditions.append("r.status IN ('dispute','platform_approved','platform_rejected','refunded')")

        if keyword:
            conditions.append("(r.refund_no LIKE %s OR r.order_no LIKE %s OR r.user LIKE %s)")
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        where = " AND ".join(conditions)

        count_rows = await self.db.execute_query(
            f"SELECT COUNT(*) FROM refund_requests r WHERE {where}", tuple(params)
        )
        total = int(count_rows[0][0]) if count_rows else 0

        params.extend([page_size, offset])
        rows = await self.db.execute_query(
            f"""SELECT r.refund_no, r.order_no, r.mall_id, r.user, r.amount, r.reason,
                       r.status, r.seller_remark, r.platform_remark, r.platform_admin,
                       r.created_at, r.reviewed_at, r.resolved_at
                FROM refund_requests r WHERE {where}
                ORDER BY r.id DESC LIMIT %s OFFSET %s""",
            tuple(params),
        )

        items = []
        for r in (rows or []):
            items.append({
                "refund_no": r[0], "order_no": r[1], "mall_id": r[2], "user": r[3],
                "amount": float(r[4]), "reason": r[5], "status": r[6],
                "seller_remark": r[7], "platform_remark": r[8], "platform_admin": r[9],
                "created_at": r[10].isoformat() if r[10] else None,
                "reviewed_at": r[11].isoformat() if r[11] else None,
                "resolved_at": r[12].isoformat() if r[12] else None,
            })

        return {"success": True, "data": items, "total": total, "page": page, "page_size": page_size}

    # ════════════════════ 卖家端订单列表 ════════════════════

    async def get_seller_order_list(self, mall_id: int, status: str | None,
                                     keyword: str | None, page: int, page_size: int) -> dict:
        offset = (page - 1) * page_size
        conditions = ["o.mall_id = %s"]
        params: list = [mall_id]

        if status:
            conditions.append("o.status = %s")
            params.append(status)
        if keyword:
            conditions.append("(o.order_no LIKE %s OR o.receiver_name LIKE %s)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        where = " AND ".join(conditions)

        count_rows = await self.db.execute_query(
            f"SELECT COUNT(*) FROM orders o WHERE {where}", tuple(params)
        )
        total = int(count_rows[0][0]) if count_rows else 0

        params.extend([page_size, offset])
        rows = await self.db.execute_query(
            f"""SELECT o.order_no, o.user, o.total_amount, o.status,
                       o.receiver_name, o.receiver_phone, o.receiver_addr,
                       o.created_at, o.paid_at, o.shipped_at, o.received_at, o.closed_at
                FROM orders o WHERE {where}
                ORDER BY o.id DESC LIMIT %s OFFSET %s""",
            tuple(params),
        )

        items = []
        for r in (rows or []):
            order_no = r[0]
            item_rows = await self.db.execute_query(
                "SELECT product_name, spec_name, price, quantity, subtotal FROM order_items WHERE order_no = %s",
                (order_no,),
            )
            products = [
                {"product_name": ir[0], "spec_name": ir[1], "price": float(ir[2]),
                 "quantity": ir[3], "subtotal": float(ir[4])}
                for ir in (item_rows or [])
            ]

            escrow_rows = await self.db.execute_query(
                "SELECT amount, platform_commission, seller_amount, status, released_at FROM escrow_account WHERE order_no = %s",
                (order_no,),
            )
            escrow = None
            if escrow_rows:
                e = escrow_rows[0]
                escrow = {
                    "amount": float(e[0]), "platform_commission": float(e[1]),
                    "seller_amount": float(e[2]), "status": e[3],
                    "released_at": e[4].isoformat() if e[4] else None,
                }

            items.append({
                "order_no": order_no, "user": r[1], "total_amount": float(r[2]),
                "status": r[3], "receiver_name": r[4], "receiver_phone": r[5],
                "receiver_addr": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
                "paid_at": r[8].isoformat() if r[8] else None,
                "shipped_at": r[9].isoformat() if r[9] else None,
                "received_at": r[10].isoformat() if r[10] else None,
                "closed_at": r[11].isoformat() if r[11] else None,
                "products": products,
                "escrow": escrow,
            })

        return {"success": True, "data": items, "total": total, "page": page, "page_size": page_size}

    # ════════════════════ 卖家资金明细 ════════════════════

    async def get_seller_escrow_list(self, mall_id: int, status: str | None,
                                      page: int, page_size: int) -> dict:
        offset = (page - 1) * page_size
        conditions = ["e.mall_id = %s"]
        params: list = [mall_id]

        if status:
            conditions.append("e.status = %s")
            params.append(status)

        where = " AND ".join(conditions)

        count_rows = await self.db.execute_query(
            f"SELECT COUNT(*) FROM escrow_account e WHERE {where}", tuple(params)
        )
        total = int(count_rows[0][0]) if count_rows else 0

        params.extend([page_size, offset])
        rows = await self.db.execute_query(
            f"""SELECT e.order_no, e.user, e.amount, e.platform_rate, e.platform_commission,
                       e.seller_amount, e.status, e.released_at, e.created_at
                FROM escrow_account e WHERE {where}
                ORDER BY e.id DESC LIMIT %s OFFSET %s""",
            tuple(params),
        )

        items = []
        for r in (rows or []):
            items.append({
                "order_no": r[0], "user": r[1], "amount": float(r[2]),
                "platform_rate": float(r[3]), "platform_commission": float(r[4]),
                "seller_amount": float(r[5]), "status": r[6],
                "released_at": r[7].isoformat() if r[7] else None,
                "created_at": r[8].isoformat() if r[8] else None,
            })

        return {"success": True, "data": items, "total": total, "page": page, "page_size": page_size}
