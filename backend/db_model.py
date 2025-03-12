import sqlite3
from datetime import datetime
import os
import uuid

class Database:
    def __init__(self, db_path="logs.db"):
        self.db_path = db_path
        self.create_tables()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 允许通过名称访问列
        return conn
    
    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            created_at TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_log(self, content, start_time=None, end_time=None):
        """添加新日志条目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        log_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 如果没有提供开始时间，使用当前时间
        if not start_time:
            start_time = now
        
        cursor.execute(
            'INSERT INTO logs (id, content, start_time, end_time, created_at) VALUES (?, ?, ?, ?, ?)',
            (log_id, content, start_time, end_time, now)
        )
        
        conn.commit()
        conn.close()
        
        return log_id
    
    def get_logs(self, days=30):
        """获取最近几天的日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 计算几天前的日期
        from datetime import timedelta
        date_limit = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute(
            'SELECT * FROM logs WHERE start_time >= ? ORDER BY start_time DESC',
            (date_limit,)
        )
        
        logs = [{
            'id': row['id'],
            'content': row['content'],
            'start_time': row['start_time'],
            'end_time': row['end_time'],
            'created_at': row['created_at']
        } for row in cursor.fetchall()]
        
        conn.close()
        
        return logs
    
    def delete_log(self, log_id):
        """删除日志条目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM logs WHERE id = ?', (log_id,))
        
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def update_log(self, log_id, content=None, start_time=None, end_time=None):
        """更新日志条目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 首先获取当前记录
        cursor.execute('SELECT * FROM logs WHERE id = ?', (log_id,))
        current = cursor.fetchone()
        
        if not current:
            conn.close()
            return False
        
        # 使用新值或保持原有值
        new_content = content if content is not None else current['content']
        new_start_time = start_time if start_time is not None else current['start_time']
        new_end_time = end_time if end_time is not None else current['end_time']
        
        cursor.execute(
            'UPDATE logs SET content = ?, start_time = ?, end_time = ? WHERE id = ?',
            (new_content, new_start_time, new_end_time, log_id)
        )
        
        updated = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return updated

# 创建全局数据库实例
db = Database()