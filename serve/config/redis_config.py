# config/redis_config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class RedisSettings(BaseSettings):
    """Redis配置类"""
    REDIS_HOST: str = Field(default='localhost', description='Redis主机地址')
    REDIS_PORT: int = Field(default=6379, description='Redis端口')
    REDIS_PASSWORD: Optional[str] = Field(default=None, description='Redis密码')
    REDIS_DB: int = Field(default=0, description='Redis数据库编号')
    REDIS_USERNAME: Optional[str] = Field(default=None, description='Redis用户名')
    REDIS_ENCODING: str = Field(default='utf-8', description='Redis编码格式')
    REDIS_DECODE_RESPONSES: bool = Field(default=True, description='是否自动解码响应')
    REDIS_MAX_CONNECTIONS: int = Field(default=200, description='最大连接数')
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, description='Socket超时时间（秒）')
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5, description='连接超时时间（秒）')
    REDIS_RETRY_ON_TIMEOUT: bool = Field(default=True, description='超时时是否重试')
    REDIS_HEALTH_CHECK_INTERVAL: int = Field(default=30, description='健康检查间隔（秒）')
    
    # Redis连接URL（自动拼接）
    @property
    def REDIS_URL(self) -> str:
        """生成Redis连接URL"""
        if self.REDIS_PASSWORD:
            if self.REDIS_USERNAME:
                return f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"          # 从.env文件读取配置
        env_file_encoding = "utf-8"  # 编码格式
        case_sensitive = False     # 忽略大小写

# 创建配置实例
settings = RedisSettings()

# 导出配置
__all__ = ["settings", "RedisSettings"]

