from flask import Flask, request, jsonify
import json
from datetime import datetime, timedelta
from flask_cors import CORS
import os
from db_model import db  # 导入数据库模型
from notion_helper import sync_to_notion, parse_text  # 从notion_helper导入函数
from openai_helper import generate_suggestion  # 导入OpenAI建议生成功能

app = Flask(__name__)
CORS(app)  # 为所有路由启用CORS

@app.route("/api/add-log", methods=["POST"])
def add_log():
    data = request.get_json()
    log_text = data["log"]
    
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
                    end_time=event['end']
                )
                log_ids.append(log_id)
                
                # 同步到Notion
                notion_id = sync_to_notion(
                    content=event['content'],
                    start_time=event['start'],
                    end_time=event['end']
                )
            
            return jsonify({"status": "success", "log_ids": log_ids})
        
    except Exception as e:
        print(f"解析事件时出错: {e}")
    
    # 如果没有事件或解析失败，添加为简单日志
    log_id = db.add_log(content=log_text)
    
    # 同步到Notion作为简单任务
    notion_id = sync_to_notion(content=log_text)
    
    return jsonify({"status": "success", "log_id": log_id, "notion_id": notion_id})

@app.route("/api/logs", methods=["GET"])
def get_logs():
    # 从URL参数获取天数，默认为30天
    days = request.args.get('days', default=30, type=int)
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
def delete_log(log_id):
    success = db.delete_log(log_id)
    
    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Log not found"}), 404

@app.route("/api/suggestion", methods=["GET"])
def suggestion():
    """使用OpenAI生成基于用户日志的建议"""
    try:
        # 直接调用OpenAI助手的建议生成功能
        suggestion_text = generate_suggestion()
        return jsonify({"suggestion": suggestion_text})
    except Exception as e:
        print(f"生成建议时出错: {e}")
        return jsonify({"suggestion": "生成建议时遇到错误，请稍后再试。"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)