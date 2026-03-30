from data.sql_client_pool import DBPool

class LogisticsService:
    def __init__(self,db:DBPool):
        self.db = db
        