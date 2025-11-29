import motor.motor_asyncio
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from config.mongodb_config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    """MongoDB异步客户端连接池"""
    
    def __init__(self):
        """初始化MongoDB客户端"""
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.database: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self._sync_client: Optional[MongoClient] = None
        
    async def connect(self) -> None:
        """异步连接到MongoDB服务器"""
        try:
            # 构建连接参数
            connection_params = {
                "maxPoolSize": settings.MONGODB_MAX_POOL_SIZE,
                "minPoolSize": settings.MONGODB_MIN_POOL_SIZE,
                "maxIdleTimeMS": settings.MONGODB_MAX_IDLE_TIME,
                "connectTimeoutMS": settings.MONGODB_CONNECT_TIMEOUT,
                "socketTimeoutMS": settings.MONGODB_SOCKET_TIMEOUT,
                "retryWrites": settings.MONGODB_RETRY_WRITES,
                "retryReads": settings.MONGODB_RETRY_READS,
            }
            
            # 创建异步客户端
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGODB_URL,
                **connection_params
            )
            
            # 获取数据库实例
            self.database = self.client[settings.MONGODB_DATABASE]
            
            # 测试连接
            await self.client.admin.command('ping')
            logger.info("MongoDB连接已建立")
            
        except Exception as e:
            logger.error(f"MongoDB连接失败: {str(e)}")
            raise
    
    def get_sync_client(self) -> MongoClient:
        """获取同步客户端（用于特殊场景）"""
        if not self._sync_client:
            self._sync_client = MongoClient(
                settings.MONGODB_URL,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxIdleTimeMS=settings.MONGODB_MAX_IDLE_TIME,
                connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT,
                socketTimeoutMS=settings.MONGODB_SOCKET_TIMEOUT,
                retryWrites=settings.MONGODB_RETRY_WRITES,
                retryReads=settings.MONGODB_RETRY_READS,
            )
        return self._sync_client
    
    async def close(self) -> None:
        """异步关闭MongoDB连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB连接已关闭")
        
        if self._sync_client:
            self._sync_client.close()
    
    def get_collection(self, collection_name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
        """获取集合实例"""
        if self.database is None:
            raise RuntimeError("MongoDB客户端未连接")
        return self.database[collection_name]
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """插入单个文档"""
        collection = self.get_collection(collection_name)
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """插入多个文档"""
        collection = self.get_collection(collection_name)
        result = await collection.insert_many(documents)
        return [str(doc_id) for doc_id in result.inserted_ids]
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查询单个文档"""
        collection = self.get_collection(collection_name)
        return await collection.find_one(filter_dict)
    
    async def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
                       limit: int = None, skip: int = None, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """查询多个文档"""
        collection = self.get_collection(collection_name)
        filter_dict = filter_dict or {}
        
        cursor = collection.find(filter_dict)
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        
        return await cursor.to_list(length=None)
    
    async def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                        update_dict: Dict[str, Any], upsert: bool = False) -> int:
        """更新单个文档"""
        collection = self.get_collection(collection_name)
        result = await collection.update_one(filter_dict, update_dict, upsert=upsert)
        return result.modified_count
    
    async def update_many(self, collection_name: str, filter_dict: Dict[str, Any], 
                         update_dict: Dict[str, Any], upsert: bool = False) -> int:
        """更新多个文档"""
        collection = self.get_collection(collection_name)
        result = await collection.update_many(filter_dict, update_dict, upsert=upsert)
        return result.modified_count
    
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """删除单个文档"""
        collection = self.get_collection(collection_name)
        result = await collection.delete_one(filter_dict)
        return result.deleted_count
    
    async def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """删除多个文档"""
        collection = self.get_collection(collection_name)
        result = await collection.delete_many(filter_dict)
        return result.deleted_count
    
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """统计文档数量"""
        collection = self.get_collection(collection_name)
        filter_dict = filter_dict or {}
        return await collection.count_documents(filter_dict)
    
    async def create_index(self, collection_name: str, keys: List[tuple], unique: bool = False) -> str:
        """创建索引"""
        collection = self.get_collection(collection_name)
        result = await collection.create_index(keys, unique=unique)
        return result
    
    async def drop_collection(self, collection_name: str) -> None:
        """删除集合"""
        collection = self.get_collection(collection_name)
        await collection.drop()
        logger.info(f"集合 {collection_name} 已删除")

# 创建全局MongoDB客户端实例
mongodb_client = MongoDBClient()

def get_mongodb_client() -> MongoDBClient:
    """获取MongoDB客户端实例"""
    return mongodb_client