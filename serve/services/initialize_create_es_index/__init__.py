from config.log_config import logger
from elasticsearch import AsyncElasticsearch
from data.es_client import get_es_client


class CreateESIndexService:

    async def show_index(self):
        es: AsyncElasticsearch = await get_es_client()
        return await es.indices.exists(index="products")

    async def create_index(self):
        try:
            es: AsyncElasticsearch = await get_es_client()

            if await self.show_index():
                logger.info("索引已存在")
                return

            await es.indices.create(index="products")
            logger.info("索引创建成功")
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise
