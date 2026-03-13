# config/jwt_config.py
from pydantic_settings import BaseSettings
from pydantic import Field


class JwtSettings(BaseSettings):
    """JWT 密钥配置（所有密钥均不低于 32 字节，满足 HS256 安全要求）"""

    # 普通用户 Token 密钥
    JWT_USER_SECRET_KEY: str = Field(
        default="xb_mall_user_jwt_secret_key_2024_hmac_sha256_secure",
        description="普通用户 JWT 签名密钥，建议通过环境变量覆盖"
    )

    # 邮箱验证码 Token 密钥
    JWT_CODE_SECRET_KEY: str = Field(
        default="xb_mall_verify_code_jwt_secret_key_2024_hmac_sha256_secure",
        description="验证码 JWT 签名密钥，建议通过环境变量覆盖"
    )

    # 管理员 Token 密钥
    JWT_ADMIN_SECRET_KEY: str = Field(
        default="xb_mall_admin_jwt_secret_key_2024_hmac_sha256_secure",
        description="管理员 JWT 签名密钥，建议通过环境变量覆盖"
    )

    # 商户 Token 密钥
    JWT_SELLER_SECRET_KEY: str = Field(
        default="xb_mall_seller_jwt_secret_key_2024_hmac_sha256_secure",
        description="商户 JWT 签名密钥，建议通过环境变量覆盖"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


jwt_settings = JwtSettings()

__all__ = ["jwt_settings", "JwtSettings"]
