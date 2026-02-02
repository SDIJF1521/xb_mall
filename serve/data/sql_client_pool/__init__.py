import aiomysql
import asyncio
from fastapi import HTTPException
from config.sql_config import settings
import logging

logger = logging.getLogger(__name__)

class DatabasePool:
    """数据库连接池管理器"""
    
    def __init__(self):
        self.pool = None
    
    async def create_pool(self):
        """创建数据库连接池"""
        try:
            self.pool = await aiomysql.create_pool(
                host=settings.DB_HOST,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                db=settings.DB_NAME,
                autocommit=True,
                minsize=10,  # 最小连接数
                maxsize=200,  # 最大连接数
                connect_timeout=10,  # 连接超时时间
                pool_recycle=3600  # 连接回收时间
            )
            logger.info("数据库连接池创建成功")
        except Exception as e:
            logger.error(f"数据库连接池创建失败: {str(e)}")
            raise
    
    async def close_pool(self):
        """关闭数据库连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("数据库连接池已关闭")
    
    async def execute_query(self, query, params=None):
        """
        执行数据库查询（使用连接池管理连接）
        自动区分SELECT查询和写操作，SELECT返回结果，写操作自动提交
        """
        if not self.pool:
            await self.create_pool()
        
        try:
            async with self.pool.acquire() as conn:
                try:
                    async with conn.cursor() as cursor:
                        await cursor.execute(query, params)
                        # 根据SQL类型决定是否返回结果
                        if query.strip().lower().startswith("select"):
                            return await cursor.fetchall()
                        else:
                            await conn.commit()  # 写操作需要提交
                            return None
                except aiomysql.Error as e:
                    logger.error(f"数据库查询错误: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
        except asyncio.CancelledError:
            # 任务被取消时重新抛出，让上层处理
            logger.debug("数据库查询被取消")
            raise

# 创建全局数据库连接池实例
db_pool = DatabasePool()

async def get_db_pool():
    """
    从连接池获取数据库连接（FastAPI依赖注入）
    如果连接池不存在，会自动创建（延迟初始化）
    注意：如果不在 main.py 的 lifespan 中管理连接池，应用关闭时可能无法正确关闭连接池
    """
    # 确保连接池已创建（延迟初始化）
    if not db_pool.pool:
        await db_pool.create_pool()
    
    # 从连接池获取连接
    async with db_pool.pool.acquire() as conn:
        try:
            yield conn
        finally:
            # 连接会自动归还到连接池，不需要手动关闭
            pass