# Text2Cal
## Demo link:
https://text2cal.vercel.app/

## Installation
Running the Frontend (Next.js)
```
cd /path/to/your/project

# Install dependencies (if you haven't already)
npm install

# Start the development server
npm run dev
```
The frontend should start and be accessible at http://localhost:3000

Running the Backend (Flask)
```
cd /path/to/your/project/backend

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies (if you haven't already)
pip install -r requirements.txt  # If you have a requirements file
# Or install manually:
pip install flask requests flask-cors openai python-dotenv

# Start the Flask server
python app.py
```
The backend should start and be accessible at http://localhost:5000

---
## List to do:
目前我的问题是，
1. 各个功能应该写在哪里？
2. 深度学习模型应该怎么建立？数据应该如何收集？需要怎么的数据？

后端功能列表

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