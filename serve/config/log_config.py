# config/log_config.py
import logging
import logging.handlers
import os
from pathlib import Path

# 项目根目录（serve）
project_root = Path(__file__).resolve().parent.parent
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "app.log"

# 调试信息（已禁用 - 减少终端输出）
# print(f"项目根目录：{project_root}")
# print(f"日志文件：{log_file}")

# 配置logger
logger = logging.getLogger("fastapi_logger")
logger.setLevel(logging.INFO)
logger.propagate = False
logger.handlers.clear()

# 格式化器
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 文件处理器
try:
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding="utf-8",
        delay=True  # 延迟创建文件
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"⚠️  文件日志初始化失败：{e}")

# 控制台处理器（已禁用 - 只输出到文件）
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# console_handler.setLevel(logging.INFO)
# logger.addHandler(console_handler)

# 初始化日志（只在第一次加载时记录）
if not getattr(logger, '_initialized', False):
    logger.info("=" * 50)
    logger.info("日志系统启动成功")
    logger.info(f"日志文件路径：{log_file}")
    logger.info("=" * 50)
    logger._initialized = True

__all__ = ["logger", "log_file"]