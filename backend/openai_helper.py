import os
from dotenv import load_dotenv
import openai
import requests
from datetime import datetime, timedelta

# 加载环境变量
load_dotenv()

def get_logs_from_notion(days=7):
    """从Notion数据库获取过去几天的日志"""
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        raise ValueError("缺少Notion API凭据。请设置NOTION_TOKEN和NOTION_DATABASE_ID环境变量。")
    
    # 计算过去7天的日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 格式化日期为ISO 8601格式
    start_date_iso = start_date.isoformat()
    
    # Notion API的查询端点
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # 构建过滤器来获取特定日期范围内的记录
    # 注意：这里假设你的Notion数据库有一个名为"Dates"的日期属性
    payload = {
        "filter": {
            "property": "Dates",
            "date": {
                "on_or_after": start_date_iso
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"获取Notion日志时出错: {response.status_code}")
        print(response.text)
        return []
    
    results = response.json().get('results', [])
    logs = []
    
    # 从结果中提取日志文本和日期
    for item in results:
        properties = item.get('properties', {})
        todo_property = properties.get('To-do', {})
        title = todo_property.get('title', [])
        
        if title:
            log_text = title[0].get('text', {}).get('content', '')
            
            # 获取日期（如果有）
            date_property = properties.get('Dates', {})
            date = date_property.get('date', {})
            date_str = date.get('start', 'No date') if date else 'No date'
            
            logs.append(f"[{date_str}] {log_text}")
    
    return logs

def generate_suggestion():
    """生成基于过去日志的AI建议"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("缺少OpenAI API密钥。请设置OPENAI_API_KEY环境变量。")
    
    # 获取过去7天的日志
    try:
        logs = get_logs_from_notion(7)
        
        if not logs:
            return "没有找到过去7天的日志记录。请添加一些日志，然后再试一次。"
        
        logs_text = "\n".join(logs)
        
        # 构建提示
        prompt = f"""以下是过去7天的日志记录：

{logs_text}
作为我的时间管理助手，帮我分析及审视我的日程安排，并提供以下方面的建议（如有）：
1. 时间管理模式
2. 效率提升机会
3. 重复任务自动化的可能性
4. 其他可能的改进建议

请提供具体、可操作的建议，帮助我提高工作效率， 回答在3句子以内。"""
        
        # 使用兼容性更强的方式初始化OpenAI客户端
        openai.api_key = api_key
        
        # 使用旧版API调用方式
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位专业的效率顾问，专注于帮助用户分析他们的日常活动并提供改进建议。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message['content']
    
    except Exception as e:
        print(f"调用OpenAI API时出错: {e}")
        return f"目前无法生成建议。错误: {str(e)}"