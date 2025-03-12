from flask import Flask, request, jsonify
import json
import re
from datetime import datetime, timedelta
from flask_cors import CORS
import os
from db_model import db  # 导入数据库模型
from notion_helper import sync_to_notion, parse_text  # 导入Notion同步函数

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
    
    # 同步到Notion
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
    # 这里可以添加生成建议的代码
    # 你可以使用SQLite数据库中的数据来生成建议
    try:
        logs = db.get_logs(days=7)  # 获取最近7天的日志
        
        if not logs:
            return jsonify({"suggestion": "没有找到过去7天的日志记录。请添加一些日志，然后再试一次。"})
        
        # 这里你可以根据日志数据生成一些简单的建议
        # 例如，找出最常见的活动，或者检测时间模式等
        
        # 简单示例，只返回日志数量和一般性建议
        log_count = len(logs)
        
        suggestion_text = f"""
过去7天我记录了{log_count}个日志项目。
日志：{logs}
根据我的记录，给我一些建议（3句以内）。
"""
        
        return jsonify({"suggestion": suggestion_text})
    except Exception as e:
        print(f"生成建议时出错: {e}")
        return jsonify({"suggestion": "生成建议时遇到错误，请稍后再试。"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)