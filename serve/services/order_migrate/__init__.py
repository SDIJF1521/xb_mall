import logging
import warnings

logger = logging.getLogger(__name__)


async def run_order_migration(db_pool) -> None:
    """创建订单模块所需的数据库表：orders / order_items / payment_transactions / escrow_account。"""
    warnings.filterwarnings("ignore", category=Warning, module="aiomysql")

    # ── 订单主表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id              BIGINT AUTO_INCREMENT PRIMARY KEY,
                order_no        VARCHAR(64)   NOT NULL COMMENT '订单号（全局唯一）',
                user            VARCHAR(100)  NOT NULL COMMENT '买家用户名',
                mall_id         INT           NOT NULL COMMENT '店铺ID',
                total_amount    DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '订单总金额',
                status          ENUM('pending','paid','shipped','received','closed','refunded')
                                              NOT NULL DEFAULT 'pending' COMMENT '订单状态',
                address_id      INT           DEFAULT NULL COMMENT '收货地址ID',
                receiver_name   VARCHAR(100)  DEFAULT NULL COMMENT '收货人',
                receiver_phone  VARCHAR(20)   DEFAULT NULL COMMENT '收货电话',
                receiver_addr   VARCHAR(500)  DEFAULT NULL COMMENT '收货地址',
                remark          VARCHAR(500)  DEFAULT NULL COMMENT '买家备注',
                version         INT           NOT NULL DEFAULT 0 COMMENT '乐观锁版本号',
                expire_at       DATETIME      NOT NULL COMMENT '支付截止时间（下单+15min）',
                paid_at         DATETIME      DEFAULT NULL COMMENT '支付时间',
                shipped_at      DATETIME      DEFAULT NULL COMMENT '发货时间',
                received_at     DATETIME      DEFAULT NULL COMMENT '确认收货时间',
                closed_at       DATETIME      DEFAULT NULL COMMENT '关闭/取消时间',
                created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_order_no (order_no),
                INDEX idx_user_status (user, status),
                INDEX idx_expire (status, expire_at),
                INDEX idx_mall (mall_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单主表'
            """
        )
        logger.info("orders 表已就绪")
    except Exception as e:
        logger.warning("orders 创建跳过或失败: %s", e)

    # ── 订单明细表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id               BIGINT AUTO_INCREMENT PRIMARY KEY,
                order_id         BIGINT        NOT NULL COMMENT '订单ID',
                order_no         VARCHAR(64)   NOT NULL COMMENT '订单号',
                mall_id          INT           NOT NULL COMMENT '店铺ID',
                shopping_id      INT           NOT NULL COMMENT '商品ID',
                specification_id INT           NOT NULL COMMENT '规格ID',
                product_name     VARCHAR(200)  DEFAULT NULL COMMENT '下单时商品名称快照',
                spec_name        VARCHAR(200)  DEFAULT NULL COMMENT '下单时规格名称快照',
                price            DECIMAL(12,2) NOT NULL COMMENT '下单时单价',
                quantity         INT           NOT NULL COMMENT '购买数量',
                subtotal         DECIMAL(12,2) NOT NULL COMMENT '小计金额',
                INDEX idx_order_id (order_id),
                INDEX idx_order_no (order_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细表'
            """
        )
        logger.info("order_items 表已就绪")
    except Exception as e:
        logger.warning("order_items 创建跳过或失败: %s", e)

    # ── 支付流水表（幂等性保障） ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS payment_transactions (
                id              BIGINT AUTO_INCREMENT PRIMARY KEY,
                transaction_no  VARCHAR(64)   NOT NULL COMMENT '支付流水号（全局唯一，幂等键）',
                order_no        VARCHAR(64)   NOT NULL COMMENT '关联订单号',
                user            VARCHAR(100)  NOT NULL COMMENT '付款用户',
                amount          DECIMAL(12,2) NOT NULL COMMENT '支付金额',
                pay_method      VARCHAR(32)   DEFAULT 'alipay' COMMENT '支付方式',
                status          ENUM('pending','success','failed','refunded')
                                              NOT NULL DEFAULT 'pending' COMMENT '流水状态',
                trade_no        VARCHAR(128)  DEFAULT NULL COMMENT '第三方交易号',
                paid_at         DATETIME      DEFAULT NULL COMMENT '支付成功时间',
                refunded_at     DATETIME      DEFAULT NULL COMMENT '退款时间',
                created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_transaction_no (transaction_no),
                INDEX idx_order_no (order_no),
                INDEX idx_user (user)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付流水表'
            """
        )
        logger.info("payment_transactions 表已就绪")
    except Exception as e:
        logger.warning("payment_transactions 创建跳过或失败: %s", e)

    # ── 平台安全账户/担保交易表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS escrow_account (
                id                   BIGINT AUTO_INCREMENT PRIMARY KEY,
                order_no             VARCHAR(64)   NOT NULL COMMENT '关联订单号',
                mall_id              INT           NOT NULL COMMENT '收款店铺ID',
                user                 VARCHAR(100)  NOT NULL COMMENT '付款买家',
                amount               DECIMAL(12,2) NOT NULL COMMENT '订单总金额',
                platform_rate        DECIMAL(5,4)  NOT NULL DEFAULT 0.1000 COMMENT '平台抽成比例（默认10%）',
                platform_commission  DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '平台抽成金额',
                seller_amount        DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '卖家实收金额',
                status               ENUM('holding','released','refunded')
                                                   NOT NULL DEFAULT 'holding' COMMENT 'holding=冻结中 released=已释放给卖家 refunded=已退回买家',
                released_at          DATETIME      DEFAULT NULL COMMENT '释放时间',
                created_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_order_no (order_no),
                INDEX idx_mall (mall_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='平台担保交易账户表'
            """
        )
        logger.info("escrow_account 表已就绪")
    except Exception as e:
        logger.warning("escrow_account 创建跳过或失败: %s", e)

    # ── 退款申请表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS refund_requests (
                id              BIGINT AUTO_INCREMENT PRIMARY KEY,
                refund_no       VARCHAR(64)   NOT NULL COMMENT '退款单号（全局唯一）',
                order_no        VARCHAR(64)   NOT NULL COMMENT '关联订单号',
                mall_id         INT           NOT NULL COMMENT '店铺ID',
                user            VARCHAR(100)  NOT NULL COMMENT '申请人',
                amount          DECIMAL(12,2) NOT NULL COMMENT '退款金额',
                reason          VARCHAR(500)  DEFAULT NULL COMMENT '退款原因',
                status          ENUM('pending','approved','rejected','dispute',
                                     'platform_approved','platform_rejected','refunded')
                                              NOT NULL DEFAULT 'pending'
                                              COMMENT 'pending=待卖家审核 approved=卖家同意 rejected=卖家拒绝 dispute=平台介入中 platform_approved=平台判买家胜 platform_rejected=平台判卖家胜 refunded=退款完成',
                seller_remark   VARCHAR(500)  DEFAULT NULL COMMENT '卖家审核备注',
                platform_remark VARCHAR(500)  DEFAULT NULL COMMENT '平台仲裁备注',
                platform_admin  VARCHAR(100)  DEFAULT NULL COMMENT '处理的平台管理员',
                created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reviewed_at     DATETIME      DEFAULT NULL COMMENT '卖家审核时间',
                resolved_at     DATETIME      DEFAULT NULL COMMENT '平台仲裁/退款完成时间',
                UNIQUE KEY uk_refund_no (refund_no),
                INDEX idx_order (order_no),
                INDEX idx_mall (mall_id),
                INDEX idx_status (status),
                INDEX idx_user (user)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='退款申请表'
            """
        )
        logger.info("refund_requests 表已就绪")
    except Exception as e:
        logger.warning("refund_requests 创建跳过或失败: %s", e)

    # 兼容升级：为 orders 表扩展 refund_pending 状态
    try:
        await db_pool.execute_query(
            """ALTER TABLE orders MODIFY COLUMN status
               ENUM('pending','paid','shipped','received','closed','refunded','refund_pending')
               NOT NULL DEFAULT 'pending' COMMENT '订单状态'"""
        )
        logger.info("orders.status 已扩展 refund_pending")
    except Exception:
        pass

    # 兼容升级：为已有 escrow_account 表补充新字段
    for col, defn in [
        ("platform_rate", "DECIMAL(5,4) NOT NULL DEFAULT 0.1000 COMMENT '平台抽成比例' AFTER `amount`"),
        ("platform_commission", "DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '平台抽成金额' AFTER `platform_rate`"),
        ("seller_amount", "DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '卖家实收金额' AFTER `platform_commission`"),
    ]:
        try:
            await db_pool.execute_query(f"ALTER TABLE escrow_account ADD COLUMN {col} {defn}")
            logger.info("escrow_account 新增字段 %s", col)
        except Exception:
            pass
