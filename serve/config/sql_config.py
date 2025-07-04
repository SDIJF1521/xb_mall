from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str = 'localhost'
    DB_USER: str = 'root'
    DB_PASSWORD: str = 'root'
    DB_NAME: str = 'mall'

    class Config:
        env_file = ".env"

settings = Settings()