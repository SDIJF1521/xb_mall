"""
优惠券与活动工厂模式

使用工厂方法创建不同类型的优惠券和活动，
统一初始化流程，结合策略模式进行参数验证。
"""

import uuid
import logging
from datetime import datetime
from .strategy import get_coupon_strategy, get_activity_strategy

logger = logging.getLogger(__name__)


def _generate_no(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    short = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{ts}{short}"


# ════════════════════════════════════════════════════════════
#  优惠券工厂
# ════════════════════════════════════════════════════════════

class CouponFactory:
    """
    工厂类，根据 coupon_type 创建优惠券数据并做策略校验。
    支持平台券和商家券两种发行方式。
    """

    @staticmethod
    def create(
        name: str,
        coupon_type: str,
        issuer_type: str,
        discount_value: float,
        min_order_amount: float,
        start_time: str,
        end_time: str,
        *,
        mall_id: int | None = None,
        scope: str = "all_mall",
        platform_scope: str = "all",
        max_discount: float | None = None,
        total_count: int = 0,
        per_user_limit: int = 1,
        description: str | None = None,
        created_by: str | None = None,
        product_ids: list[dict] | None = None,
    ) -> dict:
        """
        创建优惠券数据字典。

        参数:
            name: 优惠券名称
            coupon_type: full_reduction / discount / fixed_amount
            issuer_type: platform / merchant
            discount_value: 优惠值
            min_order_amount: 最低使用金额
            start_time: 开始时间 (YYYY-MM-DD HH:MM:SS)
            end_time: 结束时间 (YYYY-MM-DD HH:MM:SS)
            mall_id: 商家ID（平台券为None）
            scope: all_mall / store / product
            platform_scope: all / merchant_choice（平台控制范围）
            max_discount: 最大优惠（折扣券用）
            total_count: 发放总量（0=不限）
            per_user_limit: 每人限领
            description: 使用说明
            created_by: 创建人
            product_ids: 适用商品列表 [{"mall_id": x, "shopping_id": y}]

        返回: {"success": True, "data": {...}} 或 {"success": False, "msg": "..."}
        """
        strategy = get_coupon_strategy(coupon_type)
        if not strategy:
            return {"success": False, "msg": f"不支持的优惠券类型: {coupon_type}"}

        coupon_data = {
            "min_order_amount": min_order_amount,
            "discount_value": discount_value,
            "max_discount": max_discount,
        }
        valid, msg = strategy.validate_coupon(coupon_data)
        if not valid:
            return {"success": False, "msg": msg}

        if issuer_type == "merchant" and mall_id is None:
            return {"success": False, "msg": "商家券必须指定店铺ID"}

        if issuer_type == "platform":
            mall_id = None

        if scope == "product" and not product_ids:
            return {"success": False, "msg": "指定商品范围时必须选择至少一个商品"}

        try:
            s_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            e_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return {"success": False, "msg": "时间格式应为 YYYY-MM-DD HH:MM:SS"}

        if e_time <= s_time:
            return {"success": False, "msg": "结束时间必须晚于开始时间"}

        coupon_no = _generate_no("CPN")

        return {
            "success": True,
            "data": {
                "coupon_no": coupon_no,
                "name": name,
                "coupon_type": coupon_type,
                "issuer_type": issuer_type,
                "mall_id": mall_id,
                "scope": scope,
                "platform_scope": platform_scope,
                "min_order_amount": min_order_amount,
                "discount_value": discount_value,
                "max_discount": max_discount,
                "total_count": total_count,
                "per_user_limit": per_user_limit,
                "start_time": start_time,
                "end_time": end_time,
                "status": "draft",
                "description": description,
                "created_by": created_by,
                "product_ids": product_ids or [],
            },
        }


# ════════════════════════════════════════════════════════════
#  活动工厂
# ════════════════════════════════════════════════════════════

class ActivityFactory:
    """
    工厂类，根据 activity_type 创建活动数据并做策略校验。
    支持平台活动和商家活动两种发起方式。
    """

    @staticmethod
    def create(
        name: str,
        activity_type: str,
        issuer_type: str,
        start_time: str,
        end_time: str,
        rules: dict,
        *,
        mall_id: int | None = None,
        platform_scope: str = "all",
        description: str | None = None,
        created_by: str | None = None,
        products: list[dict] | None = None,
        coupon_ids: list[int] | None = None,
    ) -> dict:
        """
        创建活动数据字典。

        参数:
            name: 活动名称
            activity_type: flash_sale / full_reduction / discount / group_buy
            issuer_type: platform / merchant
            start_time: 开始时间
            end_time: 结束时间
            rules: 活动规则 JSON
            mall_id: 商家ID（平台活动为None）
            platform_scope: all / merchant_choice
            description: 活动说明
            created_by: 创建人
            products: 活动商品 [{"mall_id":x, "shopping_id":y, "specification_id":z,
                                  "activity_price":p, "activity_stock":s}]
            coupon_ids: 关联优惠券ID列表

        返回: {"success": True, "data": {...}} 或 {"success": False, "msg": "..."}
        """
        strategy = get_activity_strategy(activity_type)
        if not strategy:
            return {"success": False, "msg": f"不支持的活动类型: {activity_type}"}

        valid, msg = strategy.validate_rules(rules)
        if not valid:
            return {"success": False, "msg": msg}

        if issuer_type == "merchant" and mall_id is None:
            return {"success": False, "msg": "商家活动必须指定店铺ID"}

        if issuer_type == "platform":
            mall_id = None

        try:
            s_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            e_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return {"success": False, "msg": "时间格式应为 YYYY-MM-DD HH:MM:SS"}

        if e_time <= s_time:
            return {"success": False, "msg": "结束时间必须晚于开始时间"}

        activity_no = _generate_no("ACT")

        return {
            "success": True,
            "data": {
                "activity_no": activity_no,
                "name": name,
                "activity_type": activity_type,
                "issuer_type": issuer_type,
                "mall_id": mall_id,
                "platform_scope": platform_scope,
                "start_time": start_time,
                "end_time": end_time,
                "status": "draft",
                "rules": rules,
                "description": description,
                "created_by": created_by,
                "products": products or [],
                "coupon_ids": coupon_ids or [],
            },
        }
