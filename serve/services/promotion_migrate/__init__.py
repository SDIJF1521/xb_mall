import logging
import warnings

logger = logging.getLogger(__name__)


async def run_promotion_migration(db_pool) -> None:
    """创建优惠券和活动模块所需的数据库表。"""
    warnings.filterwarnings("ignore", category=Warning, module="aiomysql")

    # ── 优惠券主表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS coupons (
                id              BIGINT AUTO_INCREMENT PRIMARY KEY,
                coupon_no       VARCHAR(64)   NOT NULL COMMENT '优惠券编号（全局唯一）',
                name            VARCHAR(200)  NOT NULL COMMENT '优惠券名称',
                coupon_type     ENUM('full_reduction','discount','fixed_amount')
                                              NOT NULL COMMENT '类型：满减/折扣/固定金额',
                issuer_type     ENUM('platform','merchant')
                                              NOT NULL COMMENT '发布方：平台/商家',
                mall_id         INT           DEFAULT NULL COMMENT '店铺ID（平台券为NULL）',
                scope           ENUM('all_mall','store','product')
                                              NOT NULL DEFAULT 'all_mall'
                                              COMMENT '适用范围：全商城/指定店铺/指定商品',
                platform_scope  ENUM('all','merchant_choice')
                                              NOT NULL DEFAULT 'all'
                                              COMMENT '平台控制范围：全商城可用/允许商家自选',
                min_order_amount DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '最低订单金额（满X元可用）',
                discount_value  DECIMAL(12,2) NOT NULL COMMENT '优惠值（满减=减免金额/折扣=折扣比例/固定=减免金额）',
                max_discount    DECIMAL(12,2) DEFAULT NULL COMMENT '最大优惠金额（折扣券用）',
                total_count     INT           NOT NULL DEFAULT 0 COMMENT '发放总量（0=不限量）',
                claimed_count   INT           NOT NULL DEFAULT 0 COMMENT '已领取数量',
                used_count      INT           NOT NULL DEFAULT 0 COMMENT '已使用数量',
                per_user_limit  INT           NOT NULL DEFAULT 1 COMMENT '每人限领数量',
                start_time      DATETIME      NOT NULL COMMENT '生效开始时间',
                end_time        DATETIME      NOT NULL COMMENT '生效结束时间',
                status          ENUM('draft','active','paused','expired')
                                              NOT NULL DEFAULT 'draft' COMMENT '状态',
                description     VARCHAR(500)  DEFAULT NULL COMMENT '使用说明',
                created_by      VARCHAR(100)  DEFAULT NULL COMMENT '创建人',
                created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_coupon_no (coupon_no),
                INDEX idx_issuer (issuer_type, status),
                INDEX idx_mall (mall_id),
                INDEX idx_time (start_time, end_time),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='优惠券主表'
            """
        )
        logger.info("coupons 表已就绪")
    except Exception as e:
        logger.warning("coupons 创建跳过或失败: %s", e)

    # ── 优惠券适用商品表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS coupon_products (
                id          BIGINT AUTO_INCREMENT PRIMARY KEY,
                coupon_id   BIGINT NOT NULL COMMENT '优惠券ID',
                mall_id     INT    NOT NULL COMMENT '店铺ID',
                shopping_id INT    NOT NULL COMMENT '商品ID',
                created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_coupon_product (coupon_id, mall_id, shopping_id),
                INDEX idx_coupon (coupon_id),
                INDEX idx_product (mall_id, shopping_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='优惠券适用商品关联表'
            """
        )
        logger.info("coupon_products 表已就绪")
    except Exception as e:
        logger.warning("coupon_products 创建跳过或失败: %s", e)

    # ── 用户优惠券表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS user_coupons (
                id         BIGINT AUTO_INCREMENT PRIMARY KEY,
                coupon_id  BIGINT       NOT NULL COMMENT '优惠券ID',
                user       VARCHAR(100) NOT NULL COMMENT '领取用户',
                status     ENUM('unused','used','expired')
                                        NOT NULL DEFAULT 'unused' COMMENT '状态',
                order_no   VARCHAR(64)  DEFAULT NULL COMMENT '使用时关联的订单号',
                claimed_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '领取时间',
                used_at    DATETIME     DEFAULT NULL COMMENT '使用时间',
                INDEX idx_user (user, status),
                INDEX idx_coupon (coupon_id),
                INDEX idx_order (order_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户优惠券表'
            """
        )
        logger.info("user_coupons 表已就绪")
    except Exception as e:
        logger.warning("user_coupons 创建跳过或失败: %s", e)

    # ── 活动主表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id              BIGINT AUTO_INCREMENT PRIMARY KEY,
                activity_no     VARCHAR(64)   NOT NULL COMMENT '活动编号（全局唯一）',
                name            VARCHAR(200)  NOT NULL COMMENT '活动名称',
                activity_type   ENUM('flash_sale','full_reduction','discount','group_buy')
                                              NOT NULL COMMENT '活动类型：秒杀/满减/折扣/拼团',
                issuer_type     ENUM('platform','merchant')
                                              NOT NULL COMMENT '发起方：平台/商家',
                mall_id         INT           DEFAULT NULL COMMENT '店铺ID（平台活动为NULL）',
                platform_scope  ENUM('all','merchant_choice')
                                              NOT NULL DEFAULT 'all'
                                              COMMENT '平台控制范围：全商城/允许商家自选加入',
                start_time      DATETIME      NOT NULL COMMENT '活动开始时间',
                end_time        DATETIME      NOT NULL COMMENT '活动结束时间',
                status          ENUM('draft','active','paused','ended')
                                              NOT NULL DEFAULT 'draft' COMMENT '状态',
                rules           JSON          DEFAULT NULL COMMENT '活动规则（JSON格式）',
                description     VARCHAR(500)  DEFAULT NULL COMMENT '活动说明',
                created_by      VARCHAR(100)  DEFAULT NULL COMMENT '创建人',
                created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_activity_no (activity_no),
                INDEX idx_issuer (issuer_type, status),
                INDEX idx_mall (mall_id),
                INDEX idx_time (start_time, end_time),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活动主表'
            """
        )
        logger.info("activities 表已就绪")
    except Exception as e:
        logger.warning("activities 创建跳过或失败: %s", e)

    # ── 活动商品表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS activity_products (
                id               BIGINT AUTO_INCREMENT PRIMARY KEY,
                activity_id      BIGINT        NOT NULL COMMENT '活动ID',
                mall_id          INT           NOT NULL COMMENT '店铺ID',
                shopping_id      INT           NOT NULL COMMENT '商品ID',
                specification_id INT           DEFAULT NULL COMMENT '规格ID（NULL=全部规格）',
                activity_price   DECIMAL(12,2) DEFAULT NULL COMMENT '活动价格',
                activity_stock   INT           DEFAULT NULL COMMENT '活动库存限制',
                sold_count       INT           NOT NULL DEFAULT 0 COMMENT '已售数量',
                joined_by        ENUM('platform','merchant')
                                               NOT NULL COMMENT '加入方：平台指定/商家自选',
                status           ENUM('active','removed')
                                               NOT NULL DEFAULT 'active' COMMENT '状态',
                created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_activity (activity_id, status),
                INDEX idx_product (mall_id, shopping_id),
                UNIQUE KEY uk_activity_product (activity_id, mall_id, shopping_id, specification_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活动商品关联表'
            """
        )
        logger.info("activity_products 表已就绪")
    except Exception as e:
        logger.warning("activity_products 创建跳过或失败: %s", e)

    # ── 活动优惠券关联表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS activity_coupons (
                id          BIGINT AUTO_INCREMENT PRIMARY KEY,
                activity_id BIGINT NOT NULL COMMENT '活动ID',
                coupon_id   BIGINT NOT NULL COMMENT '优惠券ID',
                created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_activity_coupon (activity_id, coupon_id),
                INDEX idx_activity (activity_id),
                INDEX idx_coupon (coupon_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活动优惠券关联表'
            """
        )
        logger.info("activity_coupons 表已就绪")
    except Exception as e:
        logger.warning("activity_coupons 创建跳过或失败: %s", e)

    logger.info("优惠券与活动模块表迁移完成")
