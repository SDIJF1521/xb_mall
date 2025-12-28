import motor.motor_asyncio
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from bson import ObjectId
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
        """获取集合实例
        :param collection_name: 集合名称
        :return: 集合实例
        """
        if self.database is None:
            raise RuntimeError("MongoDB客户端未连接")
        return self.database[collection_name]
    
    def _convert_objectid_to_str(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """将文档中的ObjectId转换为字符串
        :param doc: 要转换的文档
        :return: 转换后的文档或None
        """
        if doc is None:
            return None
        
        # 创建文档的副本，避免修改原始数据
        converted_doc = doc.copy()
        
        # 转换 _id 字段
        if '_id' in converted_doc and isinstance(converted_doc['_id'], ObjectId):
            converted_doc['_id'] = str(converted_doc['_id'])
        
        # 递归转换嵌套文档中的ObjectId
        for key, value in converted_doc.items():
            if isinstance(value, ObjectId):
                converted_doc[key] = str(value)
            elif isinstance(value, dict):
                converted_doc[key] = self._convert_objectid_to_str(value)
            elif isinstance(value, list):
                converted_doc[key] = [
                    self._convert_objectid_to_str(item) if isinstance(item, dict) else 
                    str(item) if isinstance(item, ObjectId) else item
                    for item in value
                ]
        
        return converted_doc
    
    def _convert_docs_objectid_to_str(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将多个文档中的ObjectId转换为字符串
        :param docs: 要转换的文档列表
        :return: 转换后的文档列表
        """
        return [self._convert_objectid_to_str(doc) for doc in docs]
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """插入单个文档
        :param collection_name: 集合名称
        :param document: 要插入的文档
        :return: 插入的文档ID
        """
        collection = self.get_collection(collection_name)
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """插入多个文档
        :param collection_name: 集合名称
        :param documents: 要插入的文档列表
        :return: 插入的文档ID列表
        """
        collection = self.get_collection(collection_name)
        result = await collection.insert_many(documents)
        return [str(doc_id) for doc_id in result.inserted_ids]
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查询单个文档
        :param collection_name: 集合名称
        :param filter_dict: 查询条件
        :return: 转换后的文档或None
        """
        collection = self.get_collection(collection_name)
        result = await collection.find_one(filter_dict)
        return self._convert_objectid_to_str(result)
    
    async def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
                       limit: int = None, skip: int = None, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """查询多个文档
        :param collection_name: 集合名称
        :param filter_dict: 查询条件
        :param limit: 限制返回文档数量
        :param skip: 跳过文档数量
        :param sort: 排序字段列表，每个元素为 (字段名, 排序方向) 元组
        :return: 转换后的文档列表
        """
        collection = self.get_collection(collection_name)
        filter_dict = filter_dict or {}
        
        cursor = collection.find(filter_dict)
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        
        results = await cursor.to_list(length=None)
        return self._convert_docs_objectid_to_str(results)
    
    async def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                        update_dict: Dict[str, Any], upsert: bool = False) -> int:
        """更新单个文档
        :param collection_name: 集合名称
        :param filter_dict: 查询条件
        :param update_dict: 更新操作
        :param upsert: 是否插入新文档
        :return: 更新的文档数量
        """
        collection = self.get_collection(collection_name)
        result = await collection.update_one(filter_dict, update_dict, upsert=upsert)
        return result.modified_count
    
    async def update_many(self, collection_name: str, filter_dict: Dict[str, Any], 
                         update_dict: Dict[str, Any], upsert: bool = False) -> int:
        """更新多个文档
        :param collection_name: 集合名称
        :param filter_dict: 查询条件
        :param update_dict: 更新操作
        :param upsert: 是否插入新文档
        :return: 更新的文档数量
        """
        collection = self.get_collection(collection_name)
        result = await collection.update_many(filter_dict, update_dict, upsert=upsert)
        return result.modified_count
    
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """删除单个文档
        :param collection_name: 集合名称
        :param filter_dict: 查询条件
        :return: 删除的文档数量
        """
        collection = self.get_collection(collection_name)
        result = await collection.delete_one(filter_dict)
        return result.deleted_count
    
    async def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """删除多个文档
        :param collection_name: 集合名称
        :param filter_dict: 查询条件
        :return: 删除的文档数量
        """
        collection = self.get_collection(collection_name)
        result = await collection.delete_many(filter_dict)
        return result.deleted_count
    
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """统计文档数量
        :param collection_name: 集合名称
        :param filter_dict: 查询条件
        :return: 文档数量
        """
        collection = self.get_collection(collection_name)
        filter_dict = filter_dict or {}
        return await collection.count_documents(filter_dict)
    
    async def create_index(self, collection_name: str, keys: List[tuple], unique: bool = False) -> str:
        """创建索引
        :param collection_name: 集合名称
        :param keys: 索引字段列表，每个元素为 (字段名, 排序方向) 元组
        :param unique: 是否唯一索引
        :return: 索引名称
        """
        collection = self.get_collection(collection_name)
        result = await collection.create_index(keys, unique=unique)
        return result
    
    async def drop_collection(self, collection_name: str) -> None:
        """删除集合
        :param collection_name: 集合名称
        """
        collection = self.get_collection(collection_name)
        await collection.drop()
        logger.info(f"集合 {collection_name} 已删除")

# 创建全局MongoDB客户端实例
mongodb_client = MongoDBClient()

def get_mongodb_client() -> MongoDBClient:
    """获取MongoDB客户端实例"""
    return mongodb_client