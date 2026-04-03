import logging
import warnings

logger = logging.getLogger(__name__)


async def run_logistics_migration(db_pool) -> None:
    """创建物流模块所需的数据库表：order_logistics。"""
    warnings.filterwarnings("ignore", category=Warning, module="aiomysql")

    # ── 物流信息表 ──
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS order_logistics (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                order_no        VARCHAR(64)   NOT NULL COMMENT '关联订单号',
                mall_id         INT           NOT NULL COMMENT '店铺ID',
                express_company VARCHAR(64)   NOT NULL DEFAULT '顺丰速运' COMMENT '快递公司名称',
                tracking_number VARCHAR(64)   NOT NULL COMMENT '快递运单号',
                sender_name     VARCHAR(64)   DEFAULT '' COMMENT '发件人姓名',
                sender_phone    VARCHAR(20)   DEFAULT '' COMMENT '发件人电话',
                sender_address  VARCHAR(512)  DEFAULT '' COMMENT '发件人地址',
                status          VARCHAR(20)   DEFAULT 'shipped' COMMENT '物流状态：shipped/in_transit/delivered',
                created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发货时间',
                updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_order_no (order_no),
                INDEX idx_mall_id (mall_id),
                INDEX idx_tracking_number (tracking_number)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单物流信息表'
            """
        )
        logger.info("order_logistics 表已就绪")
    except Exception as e:
        logger.warning("order_logistics 创建跳过或失败: %s", e)
