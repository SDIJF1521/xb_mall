import aiomysql
from fastapi import HTTPException
from config.sql_config import settings

async def get_db():
    """
    异步获取数据库连接，使用上下文管理器管理连接生命周期。
    连接成功后通过 yield 提供连接对象，最后关闭连接。
    """
    conn = await aiomysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        autocommit=True
    )
    try:
        yield conn
    finally:
        conn.close()

async def execute_db_query(conn, query, params=None):
    """
    异步执行数据库查询。
    若为 SELECT 查询，返回查询结果；其他操作在执行后提交事务。
    若出现数据库错误，抛出 HTTP 500 异常。
    """
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            if query.strip().lower().startswith("select"):
                return await cursor.fetchall()
            else:
                await conn.commit()
                return None
    except aiomysql.Error as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")