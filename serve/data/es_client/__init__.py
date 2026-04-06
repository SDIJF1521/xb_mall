from elasticsearch import AsyncElasticsearch
from config.log_config import logger
from config.es_config import es_config


class ElasticSearchClient:
    def __init__(self):
        self.client: AsyncElasticsearch | None = None

    async def init(self):
        if self.client is None:
            self.client = AsyncElasticsearch(
                                                hosts=es_config.es_hosts,
                                                basic_auth=(es_config.USERNAME, es_config.PASSWORD),

                                                verify_certs=False,     # 🔥 必加（解决 TLS 报错）
                                                ssl_show_warn=False,    # 🔥 可选（去掉警告）

                                                connections_per_node=es_config.CONNECTIONS_PER_NODE,
                                                request_timeout=es_config.REQUEST_TIMEOUT,
                                                max_retries=es_config.MAX_RETRIES,
                                                retry_on_timeout=False
                                            )
            logger.info("Elasticsearch客户端初始化完成")

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch客户端已关闭")


# 单例
es_client = ElasticSearchClient()


# ✅ 正确获取方式（统一入口）
async def get_es_client() -> AsyncElasticsearch:
    if es_client.client is None:
        await es_client.init()
    return es_client.client
