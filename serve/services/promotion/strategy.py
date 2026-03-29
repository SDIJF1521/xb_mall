"""
优惠券与活动策略模式

每种优惠券类型和活动类型对应一个策略类，封装各自的计算逻辑和验证规则。
"""

from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
#  优惠券策略（Coupon Strategy）
# ════════════════════════════════════════════════════════════

class CouponStrategy(ABC):
    """优惠券策略基类"""

    @abstractmethod
    def calculate_discount(self, order_amount: Decimal, coupon_data: dict) -> Decimal:
        """计算优惠金额，返回实际减免数额"""

    @abstractmethod
    def validate_coupon(self, coupon_data: dict) -> tuple[bool, str]:
        """验证优惠券配置是否合法"""

    def check_min_order(self, order_amount: Decimal, min_amount: Decimal) -> bool:
        return order_amount >= min_amount

    def check_time_range(self, coupon_data: dict) -> bool:
        now = datetime.now()
        start = coupon_data.get("start_time")
        end = coupon_data.get("end_time")
        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        if isinstance(end, str):
            end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        if start and end:
            return start <= now <= end
        return False


class FullReductionStrategy(CouponStrategy):
    """满减策略：订单满X元减Y元"""

    def calculate_discount(self, order_amount: Decimal, coupon_data: dict) -> Decimal:
        min_amount = Decimal(str(coupon_data.get("min_order_amount", 0)))
        discount = Decimal(str(coupon_data.get("discount_value", 0)))
        if order_amount >= min_amount:
            return min(discount, order_amount)
        return Decimal("0")

    def validate_coupon(self, coupon_data: dict) -> tuple[bool, str]:
        min_amount = coupon_data.get("min_order_amount", 0)
        discount = coupon_data.get("discount_value", 0)
        if min_amount <= 0:
            return False, "满减券最低订单金额必须大于0"
        if discount <= 0:
            return False, "满减金额必须大于0"
        if discount >= min_amount:
            return False, "满减金额不能大于或等于最低订单金额"
        return True, ""


class DiscountStrategy(CouponStrategy):
    """折扣策略：订单满X元打Y折（discount_value 为折扣比例，如 0.85 表示85折）"""

    def calculate_discount(self, order_amount: Decimal, coupon_data: dict) -> Decimal:
        min_amount = Decimal(str(coupon_data.get("min_order_amount", 0)))
        discount_rate = Decimal(str(coupon_data.get("discount_value", 1)))
        max_discount = coupon_data.get("max_discount")

        if order_amount < min_amount:
            return Decimal("0")

        discount = (order_amount * (1 - discount_rate)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if max_discount:
            max_disc = Decimal(str(max_discount))
            discount = min(discount, max_disc)

        return min(discount, order_amount)

    def validate_coupon(self, coupon_data: dict) -> tuple[bool, str]:
        discount = coupon_data.get("discount_value", 0)
        if not (0 < discount < 1):
            return False, "折扣比例必须在0到1之间（如0.85表示85折）"
        return True, ""


class FixedAmountStrategy(CouponStrategy):
    """固定金额策略：直接减固定金额（无门槛或低门槛）"""

    def calculate_discount(self, order_amount: Decimal, coupon_data: dict) -> Decimal:
        min_amount = Decimal(str(coupon_data.get("min_order_amount", 0)))
        discount = Decimal(str(coupon_data.get("discount_value", 0)))
        if order_amount >= min_amount:
            return min(discount, order_amount)
        return Decimal("0")

    def validate_coupon(self, coupon_data: dict) -> tuple[bool, str]:
        discount = coupon_data.get("discount_value", 0)
        if discount <= 0:
            return False, "固定减免金额必须大于0"
        return True, ""


# ════════════════════════════════════════════════════════════
#  活动策略（Activity Strategy）
# ════════════════════════════════════════════════════════════

class ActivityStrategy(ABC):
    """活动策略基类"""

    @abstractmethod
    def calculate_activity_price(self, original_price: Decimal, rules: dict) -> Decimal:
        """根据活动规则计算活动价格"""

    @abstractmethod
    def validate_rules(self, rules: dict) -> tuple[bool, str]:
        """验证活动规则是否合法"""

    def check_stock(self, activity_stock: int, sold_count: int) -> bool:
        if activity_stock is None or activity_stock <= 0:
            return True
        return sold_count < activity_stock


class FlashSaleStrategy(ActivityStrategy):
    """秒杀策略：指定秒杀价，限量抢购"""

    def calculate_activity_price(self, original_price: Decimal, rules: dict) -> Decimal:
        flash_price = rules.get("flash_price")
        if flash_price is not None:
            return Decimal(str(flash_price))
        discount_rate = Decimal(str(rules.get("discount_rate", 1)))
        return (original_price * discount_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def validate_rules(self, rules: dict) -> tuple[bool, str]:
        if "flash_price" not in rules and "discount_rate" not in rules:
            return False, "秒杀活动必须指定秒杀价(flash_price)或折扣率(discount_rate)"
        if "flash_price" in rules and rules["flash_price"] <= 0:
            return False, "秒杀价必须大于0"
        if "discount_rate" in rules and not (0 < rules["discount_rate"] < 1):
            return False, "折扣率必须在0到1之间"
        return True, ""


class FullReductionActivityStrategy(ActivityStrategy):
    """满减活动策略：达到门槛金额立减"""

    def calculate_activity_price(self, original_price: Decimal, rules: dict) -> Decimal:
        thresholds = rules.get("thresholds", [])
        if not thresholds:
            return original_price

        sorted_thresholds = sorted(thresholds, key=lambda x: x["min_amount"], reverse=True)
        for t in sorted_thresholds:
            if original_price >= Decimal(str(t["min_amount"])):
                reduction = Decimal(str(t["reduction"]))
                result = original_price - reduction
                return max(result, Decimal("0.01"))
        return original_price

    def validate_rules(self, rules: dict) -> tuple[bool, str]:
        thresholds = rules.get("thresholds", [])
        if not thresholds:
            return False, "满减活动必须设置至少一个梯度(thresholds)"
        for t in thresholds:
            if "min_amount" not in t or "reduction" not in t:
                return False, "每个梯度必须包含 min_amount 和 reduction"
            if t["min_amount"] <= 0 or t["reduction"] <= 0:
                return False, "门槛金额和减免金额必须大于0"
            if t["reduction"] >= t["min_amount"]:
                return False, "减免金额不能大于或等于门槛金额"
        return True, ""


class DiscountActivityStrategy(ActivityStrategy):
    """折扣活动策略：商品打折"""

    def calculate_activity_price(self, original_price: Decimal, rules: dict) -> Decimal:
        discount_rate = Decimal(str(rules.get("discount_rate", 1)))
        return (original_price * discount_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def validate_rules(self, rules: dict) -> tuple[bool, str]:
        rate = rules.get("discount_rate")
        if rate is None:
            return False, "折扣活动必须指定折扣率(discount_rate)"
        if not (0 < rate < 1):
            return False, "折扣率必须在0到1之间"
        return True, ""


class GroupBuyStrategy(ActivityStrategy):
    """拼团策略：达到指定人数享受团购价"""

    def calculate_activity_price(self, original_price: Decimal, rules: dict) -> Decimal:
        group_price = rules.get("group_price")
        if group_price is not None:
            return Decimal(str(group_price))
        discount_rate = Decimal(str(rules.get("discount_rate", 1)))
        return (original_price * discount_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def validate_rules(self, rules: dict) -> tuple[bool, str]:
        min_group = rules.get("min_group_size")
        if not min_group or min_group < 2:
            return False, "拼团活动最少参团人数(min_group_size)不能小于2"
        if "group_price" not in rules and "discount_rate" not in rules:
            return False, "拼团活动必须指定团购价(group_price)或折扣率(discount_rate)"
        return True, ""


# ════════════════════════════════════════════════════════════
#  策略上下文（统一调用入口）
# ════════════════════════════════════════════════════════════

COUPON_STRATEGIES: dict[str, CouponStrategy] = {
    "full_reduction": FullReductionStrategy(),
    "discount": DiscountStrategy(),
    "fixed_amount": FixedAmountStrategy(),
}

ACTIVITY_STRATEGIES: dict[str, ActivityStrategy] = {
    "flash_sale": FlashSaleStrategy(),
    "full_reduction": FullReductionActivityStrategy(),
    "discount": DiscountActivityStrategy(),
    "group_buy": GroupBuyStrategy(),
}


def get_coupon_strategy(coupon_type: str) -> CouponStrategy | None:
    return COUPON_STRATEGIES.get(coupon_type)


def get_activity_strategy(activity_type: str) -> ActivityStrategy | None:
    return ACTIVITY_STRATEGIES.get(activity_type)
