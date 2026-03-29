"""
营销服务层

整合策略模式和工厂模式，提供优惠券和活动的完整 CRUD 与业务操作。
- 平台端：发布通用优惠券和平台活动，管控作用范围
- 商家端：发布专属店铺/商品优惠券和活动，可选择加入平台活动
"""

import json
import logging
from datetime import datetime
from decimal import Decimal

from .factory import CouponFactory, ActivityFactory
from .strategy import get_coupon_strategy, get_activity_strategy

logger = logging.getLogger(__name__)


class PromotionService:

    def __init__(self, db_pool, redis=None):
        self.db = db_pool
        self.redis = redis

    # ════════════════════ 优惠券 CRUD ════════════════════

    async def create_coupon(self, params: dict) -> dict:
        """通过工厂创建优惠券并持久化"""
        result = CouponFactory.create(**params)
        if not result["success"]:
            return result

        data = result["data"]
        product_ids = data.pop("product_ids", [])

        await self.db.execute_query(
            """INSERT INTO coupons
               (coupon_no, name, coupon_type, issuer_type, mall_id, scope,
                platform_scope, min_order_amount, discount_value, max_discount,
                total_count, per_user_limit, start_time, end_time, status,
                description, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                data["coupon_no"], data["name"], data["coupon_type"],
                data["issuer_type"], data["mall_id"], data["scope"],
                data["platform_scope"], data["min_order_amount"],
                data["discount_value"], data["max_discount"],
                data["total_count"], data["per_user_limit"],
                data["start_time"], data["end_time"], data["status"],
                data["description"], data["created_by"],
            ),
        )

        coupon_row = await self.db.execute_query(
            "SELECT id FROM coupons WHERE coupon_no = %s", (data["coupon_no"],)
        )
        coupon_id = coupon_row[0][0]

        if product_ids:
            for p in product_ids:
                await self.db.execute_query(
                    """INSERT IGNORE INTO coupon_products
                       (coupon_id, mall_id, shopping_id)
                       VALUES (%s, %s, %s)""",
                    (coupon_id, p["mall_id"], p["shopping_id"]),
                )

        return {
            "success": True,
            "msg": "优惠券创建成功",
            "coupon_no": data["coupon_no"],
            "coupon_id": coupon_id,
        }

    async def update_coupon_status(self, coupon_id: int, status: str, operator: str | None = None) -> dict:
        """更新优惠券状态（上线/暂停/过期）"""
        allowed = {"draft", "active", "paused", "expired"}
        if status not in allowed:
            return {"success": False, "msg": f"无效状态: {status}"}

        rows = await self.db.execute_query(
            "SELECT id, status FROM coupons WHERE id = %s", (coupon_id,)
        )
        if not rows:
            return {"success": False, "msg": "优惠券不存在"}

        current_status = rows[0][1]
        transitions = {
            "draft": {"active"},
            "active": {"paused", "expired"},
            "paused": {"active", "expired"},
        }
        if status not in transitions.get(current_status, set()):
            return {"success": False, "msg": f"不允许从 {current_status} 转为 {status}"}

        await self.db.execute_query(
            "UPDATE coupons SET status = %s WHERE id = %s", (status, coupon_id)
        )
        return {"success": True, "msg": f"优惠券状态已更新为 {status}"}

    async def get_coupon_list(
        self,
        issuer_type: str | None = None,
        mall_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        where_parts = []
        params: list = []

        if issuer_type:
            where_parts.append("issuer_type = %s")
            params.append(issuer_type)
        if mall_id is not None:
            where_parts.append("mall_id = %s")
            params.append(mall_id)
        if status:
            where_parts.append("status = %s")
            params.append(status)

        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        offset = (page - 1) * page_size

        count_row = await self.db.execute_query(
            f"SELECT COUNT(*) FROM coupons {where}", tuple(params)
        )
        total = count_row[0][0] if count_row else 0

        rows = await self.db.execute_query(
            f"""SELECT id, coupon_no, name, coupon_type, issuer_type, mall_id,
                       scope, platform_scope, min_order_amount, discount_value,
                       max_discount, total_count, claimed_count, used_count,
                       per_user_limit, start_time, end_time, status,
                       description, created_by, created_at
                FROM coupons {where}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s""",
            tuple(params + [page_size, offset]),
        )

        coupon_list = []
        for r in (rows or []):
            coupon_list.append({
                "id": r[0], "coupon_no": r[1], "name": r[2],
                "coupon_type": r[3], "issuer_type": r[4], "mall_id": r[5],
                "scope": r[6], "platform_scope": r[7],
                "min_order_amount": float(r[8]), "discount_value": float(r[9]),
                "max_discount": float(r[10]) if r[10] else None,
                "total_count": r[11], "claimed_count": r[12], "used_count": r[13],
                "per_user_limit": r[14],
                "start_time": str(r[15]) if r[15] else None,
                "end_time": str(r[16]) if r[16] else None,
                "status": r[17], "description": r[18],
                "created_by": r[19],
                "created_at": str(r[20]) if r[20] else None,
            })

        return {
            "success": True, "total": total,
            "page": page, "page_size": page_size,
            "list": coupon_list,
        }

    async def get_coupon_detail(self, coupon_id: int) -> dict:
        rows = await self.db.execute_query(
            """SELECT id, coupon_no, name, coupon_type, issuer_type, mall_id,
                      scope, platform_scope, min_order_amount, discount_value,
                      max_discount, total_count, claimed_count, used_count,
                      per_user_limit, start_time, end_time, status,
                      description, created_by, created_at
               FROM coupons WHERE id = %s""",
            (coupon_id,),
        )
        if not rows:
            return {"success": False, "msg": "优惠券不存在"}

        r = rows[0]
        detail = {
            "id": r[0], "coupon_no": r[1], "name": r[2],
            "coupon_type": r[3], "issuer_type": r[4], "mall_id": r[5],
            "scope": r[6], "platform_scope": r[7],
            "min_order_amount": float(r[8]), "discount_value": float(r[9]),
            "max_discount": float(r[10]) if r[10] else None,
            "total_count": r[11], "claimed_count": r[12], "used_count": r[13],
            "per_user_limit": r[14],
            "start_time": str(r[15]) if r[15] else None,
            "end_time": str(r[16]) if r[16] else None,
            "status": r[17], "description": r[18],
            "created_by": r[19],
            "created_at": str(r[20]) if r[20] else None,
        }

        products = await self.db.execute_query(
            "SELECT mall_id, shopping_id FROM coupon_products WHERE coupon_id = %s",
            (coupon_id,),
        )
        detail["products"] = [
            {"mall_id": p[0], "shopping_id": p[1]}
            for p in (products or [])
        ]
        return {"success": True, "data": detail}

    async def delete_coupon(self, coupon_id: int) -> dict:
        rows = await self.db.execute_query(
            "SELECT status FROM coupons WHERE id = %s", (coupon_id,)
        )
        if not rows:
            return {"success": False, "msg": "优惠券不存在"}
        if rows[0][0] == "active":
            return {"success": False, "msg": "活动中的优惠券不能删除，请先暂停"}

        await self.db.execute_query("DELETE FROM coupon_products WHERE coupon_id = %s", (coupon_id,))
        await self.db.execute_query("DELETE FROM coupons WHERE id = %s", (coupon_id,))
        return {"success": True, "msg": "优惠券已删除"}

    # ════════════════════ 用户领取/使用优惠券 ════════════════════

    async def claim_coupon(self, user: str, coupon_id: int) -> dict:
        """用户领取优惠券"""
        rows = await self.db.execute_query(
            """SELECT id, coupon_type, status, total_count, claimed_count,
                      per_user_limit, start_time, end_time
               FROM coupons WHERE id = %s""",
            (coupon_id,),
        )
        if not rows:
            return {"success": False, "msg": "优惠券不存在"}

        r = rows[0]
        if r[2] != "active":
            return {"success": False, "msg": "优惠券暂不可领取"}

        now = datetime.now()
        if now < r[6] or now > r[7]:
            return {"success": False, "msg": "不在优惠券有效期内"}

        if r[3] > 0 and r[4] >= r[3]:
            return {"success": False, "msg": "优惠券已被领完"}

        user_count_rows = await self.db.execute_query(
            "SELECT COUNT(*) FROM user_coupons WHERE coupon_id = %s AND user = %s",
            (coupon_id, user),
        )
        user_count = user_count_rows[0][0] if user_count_rows else 0
        if user_count >= r[5]:
            return {"success": False, "msg": f"每人限领{r[5]}张"}

        await self.db.execute_query(
            "INSERT INTO user_coupons (coupon_id, user) VALUES (%s, %s)",
            (coupon_id, user),
        )
        await self.db.execute_query(
            "UPDATE coupons SET claimed_count = claimed_count + 1 WHERE id = %s",
            (coupon_id,),
        )
        return {"success": True, "msg": "领取成功"}

    async def get_user_coupons(self, user: str, status: str | None = None) -> dict:
        """获取用户优惠券列表"""
        where = "WHERE uc.user = %s"
        params: list = [user]
        if status:
            where += " AND uc.status = %s"
            params.append(status)

        rows = await self.db.execute_query(
            f"""SELECT uc.id, uc.coupon_id, uc.status, uc.order_no,
                       uc.claimed_at, uc.used_at,
                       c.coupon_no, c.name, c.coupon_type, c.scope,
                       c.min_order_amount, c.discount_value, c.max_discount,
                       c.start_time, c.end_time, c.issuer_type, c.mall_id
                FROM user_coupons uc
                JOIN coupons c ON c.id = uc.coupon_id
                {where}
                ORDER BY uc.claimed_at DESC""",
            tuple(params),
        )

        result = []
        for r in (rows or []):
            result.append({
                "id": r[0], "coupon_id": r[1], "status": r[2],
                "order_no": r[3],
                "claimed_at": str(r[4]) if r[4] else None,
                "used_at": str(r[5]) if r[5] else None,
                "coupon_no": r[6], "name": r[7], "coupon_type": r[8],
                "scope": r[9],
                "min_order_amount": float(r[10]),
                "discount_value": float(r[11]),
                "max_discount": float(r[12]) if r[12] else None,
                "start_time": str(r[13]) if r[13] else None,
                "end_time": str(r[14]) if r[14] else None,
                "issuer_type": r[15], "mall_id": r[16],
            })
        return {"success": True, "list": result}

    # ════════════════════ 活动 CRUD ════════════════════

    async def create_activity(self, params: dict) -> dict:
        """通过工厂创建活动并持久化"""
        result = ActivityFactory.create(**params)
        if not result["success"]:
            return result

        data = result["data"]
        products = data.pop("products", [])
        coupon_ids = data.pop("coupon_ids", [])
        rules_json = json.dumps(data["rules"], ensure_ascii=False) if data["rules"] else None

        await self.db.execute_query(
            """INSERT INTO activities
               (activity_no, name, activity_type, issuer_type, mall_id,
                platform_scope, start_time, end_time, status, rules,
                description, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                data["activity_no"], data["name"], data["activity_type"],
                data["issuer_type"], data["mall_id"], data["platform_scope"],
                data["start_time"], data["end_time"], data["status"],
                rules_json, data["description"], data["created_by"],
            ),
        )

        act_row = await self.db.execute_query(
            "SELECT id FROM activities WHERE activity_no = %s", (data["activity_no"],)
        )
        activity_id = act_row[0][0]

        activity_type = data["activity_type"]
        # 规则定价（discount_rate）和购物车级满减：activity_price 存 NULL，由规则计算
        price_by_rule = activity_type in self._RULE_PRICED_TYPES or activity_type in self._CART_LEVEL_TYPES

        joined_by = data["issuer_type"]
        for p in products:
            stored_price = None if price_by_rule else p.get("activity_price")
            await self.db.execute_query(
                """INSERT INTO activity_products
                   (activity_id, mall_id, shopping_id, specification_id,
                    activity_price, activity_stock, joined_by)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (
                    activity_id, p["mall_id"], p["shopping_id"],
                    p.get("specification_id"), stored_price,
                    p.get("activity_stock"), joined_by,
                ),
            )

        for cid in coupon_ids:
            await self.db.execute_query(
                "INSERT INTO activity_coupons (activity_id, coupon_id) VALUES (%s,%s)",
                (activity_id, cid),
            )

        return {
            "success": True,
            "msg": "活动创建成功",
            "activity_no": data["activity_no"],
            "activity_id": activity_id,
        }

    async def update_activity_status(self, activity_id: int, status: str) -> dict:
        allowed = {"draft", "active", "paused", "ended"}
        if status not in allowed:
            return {"success": False, "msg": f"无效状态: {status}"}

        rows = await self.db.execute_query(
            "SELECT id, status FROM activities WHERE id = %s", (activity_id,)
        )
        if not rows:
            return {"success": False, "msg": "活动不存在"}

        current = rows[0][1]
        transitions = {
            "draft": {"active"},
            "active": {"paused", "ended"},
            "paused": {"active", "ended"},
        }
        if status not in transitions.get(current, set()):
            return {"success": False, "msg": f"不允许从 {current} 转为 {status}"}

        await self.db.execute_query(
            "UPDATE activities SET status = %s WHERE id = %s", (status, activity_id)
        )
        return {"success": True, "msg": f"活动状态已更新为 {status}"}

    async def get_activity_list(
        self,
        issuer_type: str | None = None,
        mall_id: int | None = None,
        status: str | None = None,
        activity_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        where_parts = []
        params: list = []

        if issuer_type:
            where_parts.append("issuer_type = %s")
            params.append(issuer_type)
        if mall_id is not None:
            where_parts.append("mall_id = %s")
            params.append(mall_id)
        if status:
            where_parts.append("status = %s")
            params.append(status)
        if activity_type:
            where_parts.append("activity_type = %s")
            params.append(activity_type)

        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        offset = (page - 1) * page_size

        count_row = await self.db.execute_query(
            f"SELECT COUNT(*) FROM activities {where}", tuple(params)
        )
        total = count_row[0][0] if count_row else 0

        rows = await self.db.execute_query(
            f"""SELECT id, activity_no, name, activity_type, issuer_type,
                       mall_id, platform_scope, start_time, end_time,
                       status, rules, description, created_by, created_at
                FROM activities {where}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s""",
            tuple(params + [page_size, offset]),
        )

        activity_list = []
        for r in (rows or []):
            rules_data = None
            if r[10]:
                try:
                    rules_data = json.loads(r[10]) if isinstance(r[10], str) else r[10]
                except (json.JSONDecodeError, TypeError):
                    rules_data = r[10]
            activity_list.append({
                "id": r[0], "activity_no": r[1], "name": r[2],
                "activity_type": r[3], "issuer_type": r[4], "mall_id": r[5],
                "platform_scope": r[6],
                "start_time": str(r[7]) if r[7] else None,
                "end_time": str(r[8]) if r[8] else None,
                "status": r[9], "rules": rules_data,
                "description": r[11], "created_by": r[12],
                "created_at": str(r[13]) if r[13] else None,
            })

        return {
            "success": True, "total": total,
            "page": page, "page_size": page_size,
            "list": activity_list,
        }

    async def get_activity_detail(self, activity_id: int) -> dict:
        rows = await self.db.execute_query(
            """SELECT id, activity_no, name, activity_type, issuer_type,
                      mall_id, platform_scope, start_time, end_time,
                      status, rules, description, created_by, created_at
               FROM activities WHERE id = %s""",
            (activity_id,),
        )
        if not rows:
            return {"success": False, "msg": "活动不存在"}

        r = rows[0]
        rules_data = None
        if r[10]:
            try:
                rules_data = json.loads(r[10]) if isinstance(r[10], str) else r[10]
            except (json.JSONDecodeError, TypeError):
                rules_data = r[10]

        detail = {
            "id": r[0], "activity_no": r[1], "name": r[2],
            "activity_type": r[3], "issuer_type": r[4], "mall_id": r[5],
            "platform_scope": r[6],
            "start_time": str(r[7]) if r[7] else None,
            "end_time": str(r[8]) if r[8] else None,
            "status": r[9], "rules": rules_data,
            "description": r[11], "created_by": r[12],
            "created_at": str(r[13]) if r[13] else None,
        }

        products = await self.db.execute_query(
            """SELECT id, mall_id, shopping_id, specification_id,
                      activity_price, activity_stock, sold_count,
                      joined_by, status
               FROM activity_products
               WHERE activity_id = %s AND status = 'active'""",
            (activity_id,),
        )
        detail["products"] = [
            {
                "id": p[0], "mall_id": p[1], "shopping_id": p[2],
                "specification_id": p[3],
                "activity_price": float(p[4]) if p[4] else None,
                "activity_stock": p[5], "sold_count": p[6],
                "joined_by": p[7], "status": p[8],
            }
            for p in (products or [])
        ]

        coupons = await self.db.execute_query(
            """SELECT ac.coupon_id, c.coupon_no, c.name, c.coupon_type
               FROM activity_coupons ac
               JOIN coupons c ON c.id = ac.coupon_id
               WHERE ac.activity_id = %s""",
            (activity_id,),
        )
        detail["coupons"] = [
            {"coupon_id": c[0], "coupon_no": c[1], "name": c[2], "coupon_type": c[3]}
            for c in (coupons or [])
        ]

        return {"success": True, "data": detail}

    async def delete_activity(self, activity_id: int) -> dict:
        rows = await self.db.execute_query(
            "SELECT status FROM activities WHERE id = %s", (activity_id,)
        )
        if not rows:
            return {"success": False, "msg": "活动不存在"}
        if rows[0][0] == "active":
            return {"success": False, "msg": "进行中的活动不能删除，请先暂停或结束"}

        await self.db.execute_query(
            "DELETE FROM activity_products WHERE activity_id = %s", (activity_id,)
        )
        await self.db.execute_query(
            "DELETE FROM activity_coupons WHERE activity_id = %s", (activity_id,)
        )
        await self.db.execute_query(
            "DELETE FROM activities WHERE id = %s", (activity_id,)
        )
        return {"success": True, "msg": "活动已删除"}

    # ════════════════════ 商家加入/退出平台活动 ════════════════════

    # 价格由活动规则（discount_rate）决定的活动类型，商家不得自设 activity_price
    _RULE_PRICED_TYPES = {"flash_sale", "discount", "group_buy"}
    # 满减是购物车级别折扣，商品价格不变，activity_price 无意义
    _CART_LEVEL_TYPES = {"full_reduction"}

    async def merchant_join_activity(
        self, activity_id: int, mall_id: int, products: list[dict]
    ) -> dict:
        """商家将自己的商品加入平台活动"""
        act_rows = await self.db.execute_query(
            "SELECT id, issuer_type, platform_scope, status, activity_type FROM activities WHERE id = %s",
            (activity_id,),
        )
        if not act_rows:
            return {"success": False, "msg": "活动不存在"}

        issuer, scope, status, activity_type = (
            act_rows[0][1], act_rows[0][2], act_rows[0][3], act_rows[0][4]
        )
        if issuer != "platform":
            return {"success": False, "msg": "只能加入平台活动"}
        if status != "active":
            return {"success": False, "msg": "活动未开始或已结束"}
        if scope != "merchant_choice":
            return {"success": False, "msg": "该活动不允许商家自选加入"}

        # 规则定价和购物车级活动：activity_price 由平台规则决定，存 NULL
        price_by_rule = activity_type in self._RULE_PRICED_TYPES or activity_type in self._CART_LEVEL_TYPES

        added = 0
        for p in products:
            existing = await self.db.execute_query(
                """SELECT id FROM activity_products
                   WHERE activity_id = %s AND mall_id = %s AND shopping_id = %s
                     AND (specification_id = %s OR (specification_id IS NULL AND %s IS NULL))""",
                (activity_id, mall_id, p["shopping_id"],
                 p.get("specification_id"), p.get("specification_id")),
            )
            if existing:
                continue

            stored_price = None if price_by_rule else p.get("activity_price")
            await self.db.execute_query(
                """INSERT INTO activity_products
                   (activity_id, mall_id, shopping_id, specification_id,
                    activity_price, activity_stock, joined_by)
                   VALUES (%s,%s,%s,%s,%s,%s,'merchant')""",
                (
                    activity_id, mall_id, p["shopping_id"],
                    p.get("specification_id"), stored_price,
                    p.get("activity_stock"),
                ),
            )
            added += 1

        return {"success": True, "msg": f"已成功加入{added}个商品到活动"}

    async def merchant_leave_activity(
        self, activity_id: int, mall_id: int, shopping_ids: list[int] | None = None
    ) -> dict:
        """商家将商品从平台活动中移除"""
        if shopping_ids:
            placeholders = ",".join(["%s"] * len(shopping_ids))
            await self.db.execute_query(
                f"""UPDATE activity_products SET status = 'removed'
                    WHERE activity_id = %s AND mall_id = %s
                      AND joined_by = 'merchant'
                      AND shopping_id IN ({placeholders})""",
                (activity_id, mall_id, *shopping_ids),
            )
        else:
            await self.db.execute_query(
                """UPDATE activity_products SET status = 'removed'
                   WHERE activity_id = %s AND mall_id = %s AND joined_by = 'merchant'""",
                (activity_id, mall_id),
            )
        return {"success": True, "msg": "商品已从活动中移除"}

    # ════════════════════ 平台查看可加入的活动列表（供商家端） ════════════════════

    async def get_joinable_activities(self, page: int = 1, page_size: int = 20) -> dict:
        """获取商家可加入的平台活动列表（platform_scope=merchant_choice 且 active）"""
        offset = (page - 1) * page_size

        count_row = await self.db.execute_query(
            """SELECT COUNT(*) FROM activities
               WHERE issuer_type = 'platform' AND status = 'active'
                 AND platform_scope = 'merchant_choice'"""
        )
        total = count_row[0][0] if count_row else 0

        rows = await self.db.execute_query(
            """SELECT id, activity_no, name, activity_type, platform_scope,
                      start_time, end_time, rules, description
               FROM activities
               WHERE issuer_type = 'platform' AND status = 'active'
                 AND platform_scope = 'merchant_choice'
               ORDER BY start_time DESC
               LIMIT %s OFFSET %s""",
            (page_size, offset),
        )

        result = []
        for r in (rows or []):
            rules_data = None
            if r[7]:
                try:
                    rules_data = json.loads(r[7]) if isinstance(r[7], str) else r[7]
                except (json.JSONDecodeError, TypeError):
                    rules_data = r[7]
            result.append({
                "id": r[0], "activity_no": r[1], "name": r[2],
                "activity_type": r[3], "platform_scope": r[4],
                "start_time": str(r[5]) if r[5] else None,
                "end_time": str(r[6]) if r[6] else None,
                "rules": rules_data, "description": r[8],
            })

        return {
            "success": True, "total": total,
            "page": page, "page_size": page_size,
            "list": result,
        }

    # ════════════════════ C端可用优惠券列表 ════════════════════

    async def get_available_coupons(
        self, page: int = 1, page_size: int = 20,
        mall_id: int | None = None, shopping_id: int | None = None,
        user: str | None = None,
    ) -> dict:
        """
        获取当前可领取的优惠券列表（用于C端展示）。
        - mall_id: 筛选指定店铺可用的券（含全商城券 + 本店铺券 + 指定商品券）
        - shopping_id: 进一步筛选指定商品可用的券
        - user: 传入用户标识时，返回每张券的用户已领数量
        """
        offset = (page - 1) * page_size
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        where_parts = [
            "c.status = 'active'",
            "c.start_time <= %s",
            "c.end_time >= %s",
            "(c.total_count = 0 OR c.claimed_count < c.total_count)",
        ]
        params: list = [now, now]

        if mall_id is not None:
            if shopping_id is not None:
                where_parts.append(
                    "(c.scope = 'all_mall' OR (c.mall_id = %s AND c.scope = 'store') "
                    "OR (c.mall_id = %s AND c.scope = 'product' "
                    "    AND EXISTS (SELECT 1 FROM coupon_products cp "
                    "               WHERE cp.coupon_id = c.id AND cp.shopping_id = %s)))"
                )
                params.extend([mall_id, mall_id, shopping_id])
            else:
                where_parts.append(
                    "(c.scope = 'all_mall' OR c.mall_id = %s)"
                )
                params.append(mall_id)

        where_sql = "WHERE " + " AND ".join(where_parts)

        count_row = await self.db.execute_query(
            f"SELECT COUNT(*) FROM coupons c {where_sql}",
            tuple(params),
        )
        total = count_row[0][0] if count_row else 0

        rows = await self.db.execute_query(
            f"""SELECT c.id, c.coupon_no, c.name, c.coupon_type, c.issuer_type, c.mall_id,
                       c.scope, c.min_order_amount, c.discount_value, c.max_discount,
                       c.total_count, c.claimed_count, c.per_user_limit,
                       c.start_time, c.end_time, c.description
                FROM coupons c
                {where_sql}
                ORDER BY c.created_at DESC
                LIMIT %s OFFSET %s""",
            tuple(params + [page_size, offset]),
        )

        coupon_ids = [r[0] for r in (rows or [])]
        user_claimed_map: dict[int, int] = {}
        if user and coupon_ids:
            placeholders = ",".join(["%s"] * len(coupon_ids))
            uc_rows = await self.db.execute_query(
                f"SELECT coupon_id, COUNT(*) FROM user_coupons "
                f"WHERE user = %s AND coupon_id IN ({placeholders}) "
                f"GROUP BY coupon_id",
                tuple([user] + coupon_ids),
            )
            for uc in (uc_rows or []):
                user_claimed_map[uc[0]] = uc[1]

        result = []
        for r in (rows or []):
            cid = r[0]
            per_limit = r[12]
            user_claimed = user_claimed_map.get(cid, 0)
            stock_out = r[10] > 0 and r[11] >= r[10]

            if user:
                if user_claimed >= per_limit:
                    claim_status = "claimed"
                elif stock_out:
                    claim_status = "sold_out"
                else:
                    claim_status = "available"
            else:
                claim_status = "available" if not stock_out else "sold_out"

            result.append({
                "id": cid, "coupon_no": r[1], "name": r[2],
                "coupon_type": r[3], "issuer_type": r[4], "mall_id": r[5],
                "scope": r[6],
                "min_order_amount": float(r[7]),
                "discount_value": float(r[8]),
                "max_discount": float(r[9]) if r[9] else None,
                "total_count": r[10], "claimed_count": r[11],
                "per_user_limit": per_limit,
                "start_time": str(r[13]) if r[13] else None,
                "end_time": str(r[14]) if r[14] else None,
                "description": r[15],
                "user_claimed": user_claimed,
                "claim_status": claim_status,
            })

        return {
            "success": True, "total": total,
            "page": page, "page_size": page_size,
            "list": result,
        }

    # ════════════════════ C端下单时可用优惠券 ════════════════════

    async def get_usable_coupons(
        self, user: str, mall_id: int, order_amount: float,
        shopping_ids: list[int] | None = None,
    ) -> dict:
        """根据店铺和订单金额筛选用户已领且可使用的优惠券。
        shopping_ids: 订单商品ID列表，传入时对 scope=product 的券进行精确范围验证。
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        rows = await self.db.execute_query(
            """SELECT uc.id, uc.coupon_id, c.coupon_no, c.name, c.coupon_type,
                      c.scope, c.min_order_amount, c.discount_value, c.max_discount,
                      c.start_time, c.end_time, c.issuer_type, c.mall_id, c.description
               FROM user_coupons uc
               JOIN coupons c ON c.id = uc.coupon_id
               WHERE uc.user = %s AND uc.status = 'unused'
                 AND c.status = 'active'
                 AND c.start_time <= %s AND c.end_time >= %s
                 AND c.min_order_amount <= %s""",
            (user, now, now, order_amount),
        )

        result = []
        for r in (rows or []):
            scope = r[5]
            coupon_mall_id = r[12]
            coupon_id_val = r[1]
            usable = False
            if scope == "all_mall":
                usable = True
            elif scope == "store" and coupon_mall_id == mall_id:
                usable = True
            elif scope == "product" and coupon_mall_id == mall_id:
                if shopping_ids:
                    # 精确验证：订单中至少有一个商品在该券的适用商品范围内
                    ph = ",".join(["%s"] * len(shopping_ids))
                    cp_rows = await self.db.execute_query(
                        f"SELECT 1 FROM coupon_products WHERE coupon_id = %s AND shopping_id IN ({ph}) LIMIT 1",
                        (coupon_id_val, *shopping_ids),
                    )
                    usable = bool(cp_rows)
                else:
                    usable = True

            if not usable:
                continue

            strategy = get_coupon_strategy(r[4])
            discount = float(strategy.calculate_discount(
                Decimal(str(order_amount)),
                {"min_order_amount": float(r[6]), "discount_value": float(r[7]),
                 "max_discount": float(r[8]) if r[8] else None},
            ))

            result.append({
                "user_coupon_id": r[0], "coupon_id": r[1],
                "coupon_no": r[2], "name": r[3], "coupon_type": r[4],
                "scope": r[5],
                "min_order_amount": float(r[6]),
                "discount_value": float(r[7]),
                "max_discount": float(r[8]) if r[8] else None,
                "start_time": str(r[9]) if r[9] else None,
                "end_time": str(r[10]) if r[10] else None,
                "issuer_type": r[11], "mall_id": r[12],
                "description": r[13],
                "estimated_discount": discount,
            })

        result.sort(key=lambda x: x["estimated_discount"], reverse=True)
        return {"success": True, "list": result}

    # ════════════════════ 使用优惠券（下单时内部调用） ════════════════════

    async def use_coupon(self, user_coupon_id: int, user: str, order_no: str) -> dict:
        """标记用户优惠券为已使用"""
        rows = await self.db.execute_query(
            "SELECT id, coupon_id, user, status FROM user_coupons WHERE id = %s",
            (user_coupon_id,),
        )
        if not rows:
            return {"success": False, "msg": "优惠券不存在"}
        if rows[0][2] != user:
            return {"success": False, "msg": "无权使用此优惠券"}
        if rows[0][3] != "unused":
            return {"success": False, "msg": "优惠券已使用或已过期"}

        await self.db.execute_query(
            "UPDATE user_coupons SET status = 'used', order_no = %s, used_at = NOW() WHERE id = %s",
            (order_no, user_coupon_id),
        )
        await self.db.execute_query(
            "UPDATE coupons SET used_count = used_count + 1 WHERE id = %s",
            (rows[0][1],),
        )
        return {"success": True, "msg": "优惠券已使用"}

    # ════════════════════ C端进行中活动列表 ════════════════════

    async def get_active_activities(self, activity_type: str | None = None,
                                     page: int = 1, page_size: int = 20) -> dict:
        """获取当前进行中的活动列表（C端展示）"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        offset = (page - 1) * page_size

        where_parts = ["status = 'active'", "start_time <= %s", "end_time >= %s"]
        params: list = [now, now]

        if activity_type:
            where_parts.append("activity_type = %s")
            params.append(activity_type)

        where = "WHERE " + " AND ".join(where_parts)

        count_row = await self.db.execute_query(
            f"SELECT COUNT(*) FROM activities {where}", tuple(params)
        )
        total = count_row[0][0] if count_row else 0

        rows = await self.db.execute_query(
            f"""SELECT id, activity_no, name, activity_type, issuer_type,
                       mall_id, start_time, end_time, rules, description
                FROM activities {where}
                ORDER BY start_time DESC
                LIMIT %s OFFSET %s""",
            tuple(params + [page_size, offset]),
        )

        result = []
        for r in (rows or []):
            rules_data = None
            if r[8]:
                try:
                    rules_data = json.loads(r[8]) if isinstance(r[8], str) else r[8]
                except (json.JSONDecodeError, TypeError):
                    rules_data = r[8]
            result.append({
                "id": r[0], "activity_no": r[1], "name": r[2],
                "activity_type": r[3], "issuer_type": r[4], "mall_id": r[5],
                "start_time": str(r[6]) if r[6] else None,
                "end_time": str(r[7]) if r[7] else None,
                "rules": rules_data, "description": r[9],
            })

        return {
            "success": True, "total": total,
            "page": page, "page_size": page_size,
            "list": result,
        }
