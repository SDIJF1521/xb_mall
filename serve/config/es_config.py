class ESConfig:
    HOST = ["localhost"]        # Elasticsearch服务器的主机地址列表
    PORT = 9200                # Elasticsearch服务器的端口号，默认9200
    USERNAME = "elastic"        # Elasticsearch用户名的默认值
    PASSWORD = "WQsN2gImsUvCR589GfFc"       # Elasticsearch密码的默认值
    CONNECTIONS_PER_NODE = 10   # 每个节点的连接数，默认10
    REQUEST_TIMEOUT = 30    # 请求超时时间，单位为秒，默认30秒
    MAX_RETRIES = 3       # 请求失败时的最大重试次数，默认3次


    @property
    def es_hosts(self):
        return ['https://{}:{}'.format(host, self.PORT) for host in self.HOST]
    
es_config = ESConfig()

__all__ = ["es_config"]

    
