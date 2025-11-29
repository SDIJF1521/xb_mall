# config/sql_config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class DBSettings(BaseSettings):
    """数据库配置类"""
    DB_HOST: str = Field(default='localhost', description='数据库主机地址')
    DB_PORT: int = Field(default=3306, description='数据库端口')
    DB_USER: str = Field(default='root', description='数据库用户名')
    DB_PASSWORD: str = Field(default='root', description='数据库密码')
    DB_NAME: str = Field(default='mall', description='数据库名称')
    DB_CHARSET: str = Field(default='utf8mb4', description='数据库字符集')
    DB_ECHO: bool = Field(default=False, description='是否打印SQL语句')
    
    # 数据库连接URL（自动拼接）
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"

    class Config:
        env_file = ".env"          # 从.env文件读取配置
        env_file_encoding = "utf-8"  # 编码格式
        case_sensitive = False     # 忽略大小写

# 创建配置实例
settings = DBSettings()

# 导出配置
__all__ = ["settings", "DBSettings"]