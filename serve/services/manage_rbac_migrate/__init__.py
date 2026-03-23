import logging

logger = logging.getLogger(__name__)


async def run_manage_rbac_migration(db_pool) -> None:
    """创建 manage_role、为 manage_user 增加 role_id、种子超级管理员角色。"""
    try:
        await db_pool.execute_query(
            """
            CREATE TABLE IF NOT EXISTS manage_role (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(64) NOT NULL,
                description VARCHAR(255) DEFAULT '',
                permissions JSON NOT NULL,
                sort_order INT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
    except Exception as e:
        logger.warning("manage_role 创建跳过或失败: %s", e)

    try:
        rows = await db_pool.execute_query(
            """
            SELECT COUNT(*) AS c FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'manage_user' AND COLUMN_NAME = 'role_id'
            """
        )
        if rows and int(rows[0][0]) == 0:
            await db_pool.execute_query(
                "ALTER TABLE manage_user ADD COLUMN role_id INT NULL DEFAULT 1 AFTER password"
            )
            logger.info("已为 manage_user 添加 role_id")
    except Exception as e:
        logger.warning("manage_user.role_id 迁移: %s", e)

    try:
        await db_pool.execute_query(
            """
            INSERT IGNORE INTO manage_role (id, name, description, permissions, sort_order)
            VALUES (1, '超级管理员', '全部功能', JSON_ARRAY('*'), 0)
            """
        )
        await db_pool.execute_query("UPDATE manage_user SET role_id = 1 WHERE role_id IS NULL")
    except Exception as e:
        logger.warning("manage_role 种子数据: %s", e)
