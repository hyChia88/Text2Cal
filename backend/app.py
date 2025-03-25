from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from datetime import datetime
from functools import wraps
import os
from db_model import db
from notion_helper import sync_to_notion, parse_text
from openai_helper import generate_suggestion
import warnings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 添加请求限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# 错误处理装饰器
def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "An internal error occurred"
            }), 500
    return wrapper

@app.route("/api/add-log", methods=["POST"])
@limiter.limit("20 per minute")
@handle_errors
def add_log():
    data = request.get_json()
    if not data or "log" not in data:
        return jsonify({"status": "error", "message": "Missing log data"}), 400
    
    log_text = data["log"].strip()
    if not log_text:
        return jsonify({"status": "error", "message": "Log text cannot be empty"}), 400
    
    # 尝试解析结构化格式
    try:
        events = parse_text(log_text)
        log_ids = []
        
        if events:
            # 添加解析的事件
            for event in events:
                # 添加到本地数据库
                log_id = db.add_log(
                    content=event['content'],
                    start_time=event['start'],
                    end_time=event['end'],
                    progress=0  # 初始进度为0
                )
                log_ids.append(log_id)
                
                # 同步到Notion
                notion_id = sync_to_notion(
                    content=event['content'],
                    start_time=event['start'],
                    end_time=event['end']
                )
                
                # 生成AI反馈
                ai_feedback = generate_suggestion()
                db.update_log(log_id, ai_feedback=ai_feedback)
            
            return jsonify({"status": "success", "log_ids": log_ids})
        
    except Exception as e:
        logger.error(f"解析事件时出错: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
    
    # 如果没有事件或解析失败，添加为简单日志 (移除 progress 参数)
    try:
        log_id = db.add_log(content=log_text)
        
        # 同步到Notion作为简单任务
        notion_id = sync_to_notion(content=log_text)
        
        # 生成AI反馈
        ai_feedback = generate_suggestion()
        db.update_log(log_id, ai_feedback=ai_feedback)
        
        return jsonify({"status": "success", "log_id": log_id, "notion_id": notion_id})
    except Exception as e:
        logger.error(f"添加日志时出错: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/logs", methods=["GET"])
@limiter.limit("30 per minute")
@handle_errors
def get_logs():
    try:
        days = int(request.args.get('days', default=30))
        if days < 1 or days > 365:
            return jsonify({"status": "error", "message": "Days must be between 1 and 365"}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid days parameter"}), 400
    logs = db.get_logs(days)
    
    # 格式化日志用于前端显示
    formatted_logs = []
    for log in logs:
        start_time = datetime.fromisoformat(log['start_time'])
        
        # 格式化显示时间
        if log['end_time']:
            end_time = datetime.fromisoformat(log['end_time'])
            time_display = f"[{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}]"
        else:
            time_display = f"[{start_time.strftime('%Y-%m-%d')}]"
        
        formatted_logs.append({
            "id": log['id'],
            "content": f"{time_display} {log['content']}"
        })
    
    return jsonify({"logs": formatted_logs})

@app.route("/api/logs/<log_id>", methods=["DELETE"])
@limiter.limit("10 per minute")
@handle_errors
def delete_log(log_id):
    if not log_id:
        return jsonify({"status": "error", "message": "Log ID is required"}), 400
    success = db.delete_log(log_id)
    
    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Log not found"}), 404

@app.route("/api/logs/<log_id>/progress", methods=["PUT"])
@limiter.limit("30 per minute")
@handle_errors
def update_progress(log_id):
    data = request.get_json()
    if not data or "progress" not in data:
        return jsonify({"status": "error", "message": "Missing progress data"}), 400
    
    progress = data["progress"]
    if not isinstance(progress, (int, float)) or progress < 0 or progress > 100:
        return jsonify({"status": "error", "message": "Progress must be a number between 0 and 100"}), 400
    
    success = db.update_log(log_id, progress=progress)
    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Log not found"}), 404

@app.route("/api/suggestion", methods=["GET"])
@limiter.limit("5 per minute")
@handle_errors
def suggestion():
    """使用OpenAI生成基于用户日志的建议"""
    try:
        # 直接调用OpenAI助手的建议生成功能
        suggestion_text = generate_suggestion()
        return jsonify({"suggestion": suggestion_text})
    except Exception as e:
        print(f"生成建议时出错: {e}")
        return jsonify({"suggestion": "生成建议时遇到错误，请稍后再试。"})

# 添加健康检查端点
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# 添加根路由处理
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "message": "Text2Cal API is running",
        "endpoints": {
            "add_log": "/api/add-log",
            "get_logs": "/api/logs",
            "delete_log": "/api/logs/<log_id>",
            "update_progress": "/api/logs/<log_id>/progress",
            "suggestion": "/api/suggestion",
            "health": "/health"
        }
    })

if __name__ == "__main__":
    # 确保日志目录存在
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 添加调试模式
    app.run(host="0.0.0.0", port=5000, debug=True)