# config/mongodb_config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class MongoDBSettings(BaseSettings):
    """MongoDB配置类"""
    MONGODB_HOST: str = Field(default='localhost', description='MongoDB主机地址')
    MONGODB_PORT: int = Field(default=27017, description='MongoDB端口')
    MONGODB_USERNAME: Optional[str] = Field(default=None, description='MongoDB用户名')
    MONGODB_PASSWORD: Optional[str] = Field(default=None, description='MongoDB密码')
    MONGODB_DATABASE: str = Field(default='mall', description='MongoDB数据库名称')
    MONGODB_AUTH_DB: str = Field(default='admin', description='MongoDB认证数据库')
    MONGODB_MAX_POOL_SIZE: int = Field(default=100, description='连接池最大连接数')
    MONGODB_MIN_POOL_SIZE: int = Field(default=10, description='连接池最小连接数')
    MONGODB_MAX_IDLE_TIME: int = Field(default=30000, description='连接最大空闲时间（毫秒）')
    MONGODB_CONNECT_TIMEOUT: int = Field(default=5000, description='连接超时时间（毫秒）')
    MONGODB_SOCKET_TIMEOUT: int = Field(default=30000, description='Socket超时时间（毫秒）')
    MONGODB_RETRY_WRITES: bool = Field(default=True, description='是否重试写操作')
    MONGODB_RETRY_READS: bool = Field(default=True, description='是否重试读操作')
    
    # MongoDB连接URL（自动拼接）
    @property
    def MONGODB_URL(self) -> str:
        """生成MongoDB连接URL"""
        if self.MONGODB_USERNAME and self.MONGODB_PASSWORD:
            return f"mongodb://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}?authSource={self.MONGODB_AUTH_DB}"
        else:
            return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}"

    class Config:
        env_file = ".env"          # 从.env文件读取配置
        env_file_encoding = "utf-8"  # 编码格式
        case_sensitive = False     # 忽略大小写

# 创建配置实例
settings = MongoDBSettings()

# 导出配置
__all__ = ["settings", "MongoDBSettings"]