# A3: Log your memories

## Installation
1. Generate Synthetic Data (Optional)
To populate your system with test data:

Make sure the backend server is running
Visit http://localhost:3000
Click the "+" button in the bottom right corner
Select the number of synthetic memories to generate

2. Install Dependencies
Python 3.8 or higher
Node.js 14.0 or higher
MongoDB (optional, for persistent storage)

3. Backend Setup
- Clone the repository:
```
git clone https://github.com/yourusername/memory-log.git
cd memory-log
```

- Create and activate a virtual environment:
```
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

- Install Python dependencies:
```
pip install -r requirements.txt
```

Set up environment variables by creating a .env file:
```
CopyOPENAI_API_KEY=your_openai_api_key
MONGODB_URI=mongodb://localhost:27017/memory-log
NOTION_TOKEN=optional_notion_api_token
NOTION_DATABASE_ID=optional_notion_database_id
```

Start the backend server, The backend will run on http://localhost:5000:
```
python app.py
```

4. Frontend Setup

Navigate to the frontend directory:
```
cd frontend
```

Install Node.js dependencies:
```
npm install
```
Create a .env.local file with the following content:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000
```

Start the development server, The frontend will run on http://localhost:3000:
```
npm run dev
```

---
**Ignore below**
Backend file list:
1. 基础数据管理
   get_logs(days=30, page=1, per_page=20) - 获取指定天数内的日志记录，支持分页
   add_log(content, type=None, timestamp=None) - 添加新日志，增加类型和自定义时间戳参数
   delete_log(log_id) - 删除指定日志
   update_log(log_id, content=None, type=None, timestamp=None) - 更新日志内容或属性
   sync_to_notion(log_id=None, all_logs=False) - 同步日志到Notion数据库

2. 记忆处理与分析 (输入处理)
   日志分析：
   classify_log_type(content) - 自动分析日志内容，确定其类型（会议、设计、研究、个人等）
   extract_entities(content) - 从日志中提取关键实体（人物、地点、事件等）
   calculate_importance(log_id) - 计算日志的重要性分数
   generate_embeddings(content) - 为日志内容创建向量嵌入，用于语义搜索
   update_vector_database() - 更新并维护向量数据库索引

   文件处理：
   upload_file(file, metadata=None) - 处理上传的文件，提取相关信息
   get_uploaded_files(days=30, page=1, per_page=20) - 获取已上传的文件列表
   process_image(image_data, extract_text=True) - 处理图像文件，用OpenAI进行图像识别
   process_document(document_data) - 处理文档文件（PDF、Word等）

3. 记忆权重管理及建模
   // 自动权重计算
   get_attention_weights(days=30) - 获取记忆注意力权重
   calculate_context_vector(query, logs) - 计算查询与日志集合的上下文向量
   apply_self_attention(logs) - 应用自注意力机制来计算日志间的关联强度
   train_attention_model(logs_data) - 训练注意力模型
   load_attention_model(model_path=None) - 加载预训练的注意力模型
   
   // 手动权重管理
   update_attention_weight(log_id, weight) - 手动更新特定记忆的注意力权重
   reset_attention_weights() - 重置记忆权重到默认值

4. 记忆模式分析
   get_memory_patterns_data(days=30) - 获取记忆模式数据，用于前端可视化
   analyze_time_patterns() - 分析用户记忆的时间模式
   analyze_topic_trends(days=90) - 分析主题变化趋势
   detect_memory_anomalies() - 检测不寻常的记忆模式

5. 高级查询功能
   search_logs_by_content(query, page=1, per_page=20) - 基于内容搜索日志
   search_logs_by_semantic(query, page=1, per_page=20) - 基于语义相似性搜索日志
   get_logs_by_type(type, days=30, page=1, per_page=20) - 按类型获取日志

6. 记忆推荐与生成 (输出处理)
   get_recommended_logs(context=None, days=30, page=1, per_page=20) - 根据上下文推荐相关日志
   get_logs_by_importance(days=30, page=1, per_page=20) - 根据重要性排序日志
   generate_suggestion(context=None) - 基于记忆生成个性化建议
   recommend_daily_wallpaper(mood=None) - 基于日志分析推荐适合当天壁纸
   get_memory_network_data(log_id=None) - 获取记忆关联网络数据，用于前端可视化
   generate_labels_from_memories(days=30, count=5) - 从记忆中生成标签云数据

7. 系统管理
   cache_frequent_logs() - 缓存频繁访问的日志以提高性能
   clear_cache() - 清除缓存
   get_system_status() - 获取系统状态信息