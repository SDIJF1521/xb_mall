import logging
import warnings

logger = logging.getLogger(__name__)


async def run_ad_migration(db_pool) -> None:
    """创建广告投放申请表 ad_apply 和轮播图广告表 ad_banner。"""
    warnings.filterwarnings("ignore", category=Warning, module="aiomysql")

    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS ad_apply (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mall_id INT NOT NULL COMMENT '申请店铺ID',
                shopping_id INT NOT NULL COMMENT '推广商品ID',
                title VARCHAR(100) NOT NULL COMMENT '广告标题',
                description TEXT COMMENT '申请说明',
                img_path VARCHAR(255) DEFAULT NULL COMMENT '广告图片路径',
                duration_days INT DEFAULT 7 COMMENT '投放天数',
                status ENUM('pending','approved','rejected') DEFAULT 'pending' COMMENT '审核状态',
                reject_reason VARCHAR(255) DEFAULT NULL COMMENT '驳回原因',
                apply_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
                review_time DATETIME DEFAULT NULL COMMENT '审核时间',
                reviewer VARCHAR(50) DEFAULT NULL COMMENT '审核人',
                INDEX idx_mall_id (mall_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告投放申请表'
            """
        )
        logger.info("ad_apply 表已就绪")
    except Exception as e:
        logger.warning("ad_apply 创建跳过或失败: %s", e)

    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS ad_banner (
                id INT AUTO_INCREMENT PRIMARY KEY,
                apply_id INT DEFAULT NULL COMMENT '关联申请ID',
                mall_id INT NOT NULL COMMENT '店铺ID',
                shopping_id INT NOT NULL COMMENT '商品ID',
                title VARCHAR(100) NOT NULL COMMENT '广告标题',
                img_path VARCHAR(255) DEFAULT NULL COMMENT '广告图片',
                sort_order INT DEFAULT 0 COMMENT '排序（越小越靠前）',
                is_active TINYINT DEFAULT 1 COMMENT '是否启用 1=启用 0=禁用',
                start_time DATETIME NOT NULL COMMENT '投放开始时间',
                end_time DATETIME NOT NULL COMMENT '投放结束时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_active_sort (is_active, sort_order),
                INDEX idx_time_range (start_time, end_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='轮播图广告表'
            """
        )
        logger.info("ad_banner 表已就绪")
    except Exception as e:
        logger.warning("ad_banner 创建跳过或失败: %s", e)
