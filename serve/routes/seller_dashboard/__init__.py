"""
卖家端仪表盘路由
- GET  /seller/dashboard/summary  汇总数据（卡片 + 饼图 + 趋势 + 最近订单）
- GET  /seller/dashboard/export   导出营业报表 CSV
"""

import io
import csv
import logging
from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse

from services.verify_duter_token import VerifyDuterToken
from data.sql_client import get_db, execute_db_query
from data.sql_client_pool import db_pool
from data.redis_client import RedisClient, get_redis
from data.mongodb_client import MongoDBClient, get_mongodb_client

router = APIRouter()
logger = logging.getLogger(__name__)


async def _verify_seller(
    token: str, redis: RedisClient, db,
    requested_mall_id: int | None = None,
) -> tuple:
    """
    验证卖家身份，兼容 station=1（店主）和 station=2（店长/店员）。
    station=1 时可通过 requested_mall_id 选择查看哪个店铺。
    """
    verify = VerifyDuterToken(token, redis)
    token_data = await verify.token_data()
    if not token_data:
        return False, "Token 无效", None

    station = token_data.get("station")

    if station == "1":
        sql_data = await execute_db_query(
            db, "SELECT user FROM seller_sing WHERE user = %s", (token_data.get("user"),)
        )
        result = await verify.verify_token(sql_data=sql_data)
        if not result[0]:
            return False, "身份验证失败", None

        raw_list = token_data.get("state_id_list", [])
        state_id_list = [int(i) for i in raw_list if i]
        if requested_mall_id is not None:
            if requested_mall_id not in state_id_list:
                return False, "您没有权限查看该店铺", None
            token_data["_selected_mall_ids"] = [requested_mall_id]
        else:
            token_data["_selected_mall_ids"] = state_id_list

    elif station == "2":
        user = token_data.get("user")
        mall_id = token_data.get("mall_id")
        sql_data = await execute_db_query(
            db, "SELECT user FROM store_user WHERE user = %s AND store_id = %s",
            (user, mall_id),
        )
        result = await verify.verify_token(sql_data=sql_data)
        if not result[0]:
            return False, "身份验证失败", None

        from services.buyer_role_authority import RoleAuthorityService
        role_svc = RoleAuthorityService(
            role=token_data.get("role"), db=db, redis=redis,
            name=user, mall_id=mall_id,
        )
        role_authority = await role_svc.get_authority(mall_id)
        if not role_authority:
            return False, "未找到角色权限", None
        perms = await role_svc.authority_resolver(int(role_authority[0][0]))
        if not perms or not perms[2]:
            return False, "您没有查看仪表盘的权限", None

        token_data["_selected_mall_ids"] = [mall_id]
    else:
        return False, "未知的身份类型", None

    return True, "ok", token_data


def _extract_mall_ids(payload: dict) -> list[int]:
    selected = payload.get("_selected_mall_ids")
    if selected:
        return selected
    station = payload.get("station")
    if station == "2":
        mid = payload.get("mall_id")
        return [mid] if mid else []
    id_list = payload.get("state_id_list")
    if id_list and isinstance(id_list, list):
        return [int(i) for i in id_list if i]
    return []


def _build_date_range(period: str) -> tuple[datetime, datetime]:
    now = datetime.now()
    end = now
    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    elif period == "three_months":
        start = now - timedelta(days=90)
    elif period == "year":
        start = now - timedelta(days=365)
    else:
        start = now - timedelta(days=30)
    return start, end


@router.get("/seller/dashboard/summary")
async def seller_dashboard_summary(
    period: str = Query("month", description="week / month / three_months / year"),
    mall_id: int | None = Query(None, description="店主指定查看的店铺ID"),
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db, requested_mall_id=mall_id)
    if not ok:
        return {"success": False, "msg": msg}

    mall_ids = _extract_mall_ids(payload)
    if not mall_ids:
        return {"success": False, "msg": "无法确定所属店铺"}

    try:
        data = await _aggregate(mall_ids, period, mongodb, db_pool)
        return {"success": True, **data}
    except Exception as e:
        logger.error("卖家仪表盘查询失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"查询失败: {str(e)}"}


async def _aggregate(mall_ids: list[int], period: str, mongo: MongoDBClient, db) -> dict:
    start, end = _build_date_range(period)
    placeholders = ",".join(["%s"] * len(mall_ids))
    start_str = start.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end.strftime("%Y-%m-%d %H:%M:%S")

    # ── 1. 数据卡片 ──
    product_count = 0
    for mid in mall_ids:
        cnt = await mongo.count_documents("shopping", {"mall_id": mid, "audit": 1})
        product_count += cnt

    order_count_rows = await db.execute_query(
        f"SELECT COUNT(*) FROM orders WHERE mall_id IN ({placeholders}) AND created_at BETWEEN %s AND %s",
        (*mall_ids, start_str, end_str),
    )
    order_count = order_count_rows[0][0] if order_count_rows else 0

    sales_rows = await db.execute_query(
        f"""SELECT COALESCE(SUM(total_amount), 0) FROM orders
            WHERE mall_id IN ({placeholders}) AND status IN ('paid','shipped','received')
            AND created_at BETWEEN %s AND %s""",
        (*mall_ids, start_str, end_str),
    )
    total_sales = float(sales_rows[0][0]) if sales_rows else 0

    refund_rows = await db.execute_query(
        f"""SELECT COUNT(*) FROM refund_requests
            WHERE mall_id IN ({placeholders}) AND status = 'pending'""",
        tuple(mall_ids),
    )
    pending_refund = refund_rows[0][0] if refund_rows else 0

    cards = {
        "product_count": product_count,
        "order_count": order_count,
        "total_sales": round(total_sales, 2),
        "pending_refund": pending_refund,
    }

    # ── 2. 饼图：订单状态分布 ──
    status_rows = await db.execute_query(
        f"""SELECT status, COUNT(*) FROM orders
            WHERE mall_id IN ({placeholders}) AND created_at BETWEEN %s AND %s
            GROUP BY status""",
        (*mall_ids, start_str, end_str),
    )
    status_map = {
        "pending": "待支付",
        "paid": "已支付",
        "shipped": "已发货",
        "received": "已收货",
        "closed": "已关闭",
        "refunded": "已退款",
        "refund_pending": "退款中",
    }
    pie_data = [
        {"name": status_map.get(r[0], r[0]), "value": r[1]}
        for r in (status_rows or [])
    ]

    # ── 3. 折线图：销售趋势 ──
    if period == "week":
        group_fmt = "%Y-%m-%d"
    elif period in ("month", "three_months"):
        group_fmt = "%Y-%m-%d"
    else:
        group_fmt = "%Y-%m"

    trend_rows = await db.execute_query(
        f"""SELECT DATE_FORMAT(created_at, %s) AS d, COALESCE(SUM(total_amount), 0)
            FROM orders
            WHERE mall_id IN ({placeholders}) AND status IN ('paid','shipped','received')
            AND created_at BETWEEN %s AND %s
            GROUP BY d ORDER BY d""",
        (group_fmt, *mall_ids, start_str, end_str),
    )
    trend_data = [
        {"date": r[0], "sales": round(float(r[1]), 2)}
        for r in (trend_rows or [])
    ]

    # ── 4. 最近订单 ──
    recent_rows = await db.execute_query(
        f"""SELECT o.order_no, o.total_amount, o.status, o.created_at, o.user
            FROM orders o
            WHERE o.mall_id IN ({placeholders})
            ORDER BY o.created_at DESC LIMIT 10""",
        tuple(mall_ids),
    )
    recent_orders = []
    for r in (recent_rows or []):
        items = await db.execute_query(
            "SELECT product_name, quantity FROM order_items WHERE order_no = %s",
            (r[0],),
        )
        recent_orders.append({
            "order_no": r[0],
            "total_amount": float(r[1]),
            "status": r[2],
            "status_text": status_map.get(r[2], r[2]),
            "created_at": str(r[3]) if r[3] else None,
            "user": r[4],
            "items": [{"name": it[0], "qty": it[1]} for it in (items or [])],
        })

    return {
        "cards": cards,
        "pie": pie_data,
        "trend": trend_data,
        "recent_orders": recent_orders,
    }


# ════════════════════ 导出营业报表 ════════════════════

STATUS_MAP = {
    "pending": "待支付",
    "paid": "已支付",
    "shipped": "已发货",
    "received": "已收货",
    "closed": "已关闭",
    "refunded": "已退款",
    "refund_pending": "退款中",
}


@router.get("/seller/dashboard/export")
async def seller_dashboard_export(
    period: str = Query("month", description="week / month / three_months / year"),
    mall_id: int | None = Query(None, description="店主指定导出的店铺ID"),
    access_token: str = Header(..., alias="Access-Token"),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb_client),
    db=Depends(get_db),
):
    ok, msg, payload = await _verify_seller(access_token, redis, db, requested_mall_id=mall_id)
    if not ok:
        return {"success": False, "msg": msg}

    mall_ids = _extract_mall_ids(payload)
    if not mall_ids:
        return {"success": False, "msg": "无法确定所属店铺"}

    try:
        content = await _build_report_csv(mall_ids, period, db_pool)
        start, end = _build_date_range(period)
        filename = f"营业报表_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.csv"
        encoded = quote(filename)

        return StreamingResponse(
            content,
            media_type="text/csv; charset=utf-8-sig",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
            },
        )
    except Exception as e:
        logger.error("导出营业报表失败: %s", e, exc_info=True)
        return {"success": False, "msg": f"导出失败: {str(e)}"}


async def _build_report_csv(mall_ids: list[int], period: str, db) -> io.BytesIO:
    start, end = _build_date_range(period)
    placeholders = ",".join(["%s"] * len(mall_ids))
    start_str = start.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end.strftime("%Y-%m-%d %H:%M:%S")

    # ── 汇总行 ──
    summary_row = await db.execute_query(
        f"""SELECT COUNT(*),
                   COALESCE(SUM(CASE WHEN status IN ('paid','shipped','received') THEN total_amount ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN status = 'refunded' THEN total_amount ELSE 0 END), 0)
            FROM orders
            WHERE mall_id IN ({placeholders}) AND created_at BETWEEN %s AND %s""",
        (*mall_ids, start_str, end_str),
    )
    total_orders = summary_row[0][0] if summary_row else 0
    total_sales = float(summary_row[0][1]) if summary_row else 0
    total_refund = float(summary_row[0][2]) if summary_row else 0

    # ── 订单明细 ──
    order_rows = await db.execute_query(
        f"""SELECT o.order_no, o.user, o.total_amount, o.status, o.created_at,
                   o.paid_at, o.receiver_name, o.receiver_phone, o.receiver_addr, o.remark
            FROM orders o
            WHERE o.mall_id IN ({placeholders}) AND o.created_at BETWEEN %s AND %s
            ORDER BY o.created_at DESC""",
        (*mall_ids, start_str, end_str),
    )

    items_cache: dict[str, list] = {}
    if order_rows:
        order_nos = [r[0] for r in order_rows]
        nos_ph = ",".join(["%s"] * len(order_nos))
        item_rows = await db.execute_query(
            f"""SELECT order_no, product_name, spec_name, price, quantity, subtotal
                FROM order_items WHERE order_no IN ({nos_ph})""",
            tuple(order_nos),
        )
        for it in (item_rows or []):
            items_cache.setdefault(it[0], []).append(it)

    # ── 写 CSV ──
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["营业报表"])
    writer.writerow([f"统计周期: {start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"])
    writer.writerow([])
    writer.writerow(["汇总"])
    writer.writerow(["总订单数", "销售额(元)", "退款额(元)"])
    writer.writerow([total_orders, f"{total_sales:.2f}", f"{total_refund:.2f}"])
    writer.writerow([])

    writer.writerow(["订单明细"])
    writer.writerow([
        "订单号", "买家", "商品", "订单金额(元)", "状态",
        "下单时间", "支付时间", "收货人", "收货电话", "收货地址", "备注",
    ])

    for r in (order_rows or []):
        order_no = r[0]
        items = items_cache.get(order_no, [])
        product_desc = "; ".join(
            f"{it[1]}({it[2]}) x{it[4]} ¥{float(it[5]):.2f}" for it in items
        ) if items else ""

        writer.writerow([
            order_no,
            r[1],
            product_desc,
            f"{float(r[2]):.2f}",
            STATUS_MAP.get(r[3], r[3]),
            str(r[4]) if r[4] else "",
            str(r[5]) if r[5] else "",
            r[6] or "",
            r[7] or "",
            r[8] or "",
            r[9] or "",
        ])

    # UTF-8 BOM 让 Excel 正确识别中文
    result = io.BytesIO()
    result.write(b"\xef\xbb\xbf")
    result.write(buf.getvalue().encode("utf-8"))
    result.seek(0)
    return result
