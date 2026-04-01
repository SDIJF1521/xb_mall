from data.sql_client_pool import DBPool

# 定义物流服务类
class LogisticsService:
    def __init__(self,db:DBPool):
        self.db = db
        