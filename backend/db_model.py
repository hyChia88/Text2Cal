from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure
from time import sleep
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 从环境变量获取MongoDB连接字符串
MONGODB_URI = os.getenv("MONGODB_URI")

# 如果没有配置MongoDB URI，提供有用的错误信息
if not MONGODB_URI:
    print("警告: 没有设置MONGODB_URI环境变量。请确保在.env文件中设置，否则数据将无法持久化存储。")
    print("示例格式: MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database")
    # 用于开发环境的默认本地MongoDB连接
    MONGODB_URI = "mongodb://localhost:27017/text2cal"

def get_mongodb_connection(max_retries=3, retry_delay=1):
    """建立MongoDB连接，支持重试机制"""
    for attempt in range(max_retries):
        try:
            client = MongoClient(MONGODB_URI)
            # 测试连接
            client.admin.command('ping')
            return client
        except ConnectionFailure as e:
            if attempt == max_retries - 1:
                raise e
            print(f"连接尝试 {attempt + 1} 失败，{retry_delay} 秒后重试...")
            sleep(retry_delay)

# 使用重试机制建立连接
try:
    client = get_mongodb_connection()
    db_name = os.getenv("MONGODB_DB_NAME", "text2cal")
    mongo_db = client[db_name]
    logs_collection = mongo_db["logs"]
    
    # 创建索引以优化查询性能
    logs_collection.create_index("start_time")
    logs_collection.create_index([("start_time", -1)])
    logs_collection.create_index("id", unique=True)
    
    print(f"MongoDB连接成功: {db_name}")
except Exception as e:
    print(f"MongoDB连接错误: {e}")
    # 当无法连接MongoDB时，你可以实现一个备用存储方案
    # 但这里我们只打印错误信息

class Database:
    def __init__(self):
        self.collection = logs_collection
    
    def add_log(self, content, start_time=None, end_time=None, progress=0, tags=None):
        """添加新日志条目"""
        try:
            log_id = str(ObjectId())
            now = datetime.now().isoformat()
            
            if not start_time:
                start_time = now
            
            log_document = {
                "id": log_id,
                "content": content,
                "start_time": start_time,
                "end_time": end_time,
                "created_at": now,
                "progress": progress,
                "ai_feedback": None,
                "tags": tags if tags is not None else [],
            }
            
            self.collection.insert_one(log_document)
            return log_id
        except Exception as e:
            logger.error(f"添加日志失败: {e}")
            raise
    
    def get_logs(self, days=30):
        """获取最近几天的日志"""
        try:
            date_limit = (datetime.now() - timedelta(days=days)).isoformat()
            cursor = self.collection.find(
                {"start_time": {"$gte": date_limit}},
                sort=[("start_time", -1)]
            )
            
            logs = []
            for doc in cursor:
                doc.pop('_id', None)
                # Ensure all fields are present
                doc.setdefault('progress', 0)
                doc.setdefault('ai_feedback', None)
                logs.append(doc)
            
            return logs
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []
    
    def delete_log(self, log_id):
        """删除日志条目"""
        result = self.collection.delete_one({"id": log_id})
        return result.deleted_count > 0
    
    def update_log(self, log_id, content=None, start_time=None, end_time=None, progress=None, ai_feedback=None):
        """更新日志条目"""
        # 构建更新文档
        update_fields = {}
        if content is not None:
            update_fields["content"] = content
        if start_time is not None:
            update_fields["start_time"] = start_time
        if end_time is not None:
            update_fields["end_time"] = end_time
        if progress is not None:
            update_fields["progress"] = progress
        if ai_feedback is not None:
            update_fields["ai_feedback"] = ai_feedback
        
        # 只有当有字段需要更新时才进行操作
        if update_fields:
            result = self.collection.update_one(
                {"id": log_id},
                {"$set": update_fields}
            )
            return result.modified_count > 0
        
        return False
    
    def get_log(self, log_id):
        """根据ID获取单个日志"""
        doc = self.collection.find_one({"id": log_id})
        if doc:
            doc.pop('_id', None)  # 移除内部MongoDB ID
            return doc
        return None

# 创建全局数据库实例
db = Database()