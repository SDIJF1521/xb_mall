# config/scheduler_config.py
from pydantic_settings import BaseSettings
from pydantic import Field

class SchedulerSettings(BaseSettings):
    """定时任务配置类"""
    SCHEDULER_ENABLED: bool = Field(default=True, description="是否启用定时任务")
    SCHEDULER_TIMEZONE: str = Field(default="Asia/Shanghai", description="定时任务时区")
    
    # 定时任务配置
    TASK_INTERVAL_MINUTES: int = Field(default=5, description="任务执行间隔（分钟）")
    TASK_MAX_INSTANCES: int = Field(default=1, description="同一任务最大并发实例数")
    TASK_COALESCE: bool = Field(default=True, description="是否合并任务")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# 创建配置实例
scheduler_settings = SchedulerSettings()

# 导出配置
__all__ = ["scheduler_settings", "SchedulerSettings"]