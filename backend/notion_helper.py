import requests
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def parse_text(text):
    """
    解析文本输入，格式为:
    @dd/mm/yy start_time-end_time: [To-do]
    
    可以输入多个同一日期的事件:
    @dd/mm/yy start_time-end_time: [To-do]
    start_time-end_time: [To-do]
    start_time-end_time: [To-do]
    
    返回包含'start'、'end'和'content'键的事件字典列表
    """
    lines = text.strip().split('\n')
    events = []
    current_date = None
    
    date_pattern = r'@(\d{1,2}/\d{1,2}/\d{2})'
    time_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检查这行是否指定了新日期
        date_match = re.search(date_pattern, line)
        if date_match:
            date_str = date_match.group(1)
            try:
                # 将日期字符串解析为datetime对象
                current_date = datetime.strptime(date_str, "%d/%m/%y")
            except ValueError:
                print(f"无效的日期格式: {date_str}。使用今天的日期。")
                current_date = datetime.now()
        
        # 如果行中没有找到日期且没有之前的日期，则使用今天
        if current_date is None:
            current_date = datetime.now()
        
        # 提取时间和内容
        # 查找格式为"9:00-10:30: 与团队会议"的时间模式
        time_content_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2}):\s*(.+)'
        time_match = re.search(time_content_pattern, line)
        
        if time_match:
            start_hour, start_min, end_hour, end_min, content = time_match.groups()
            
            # 创建开始和结束datetime对象
            start_datetime = current_date.replace(
                hour=int(start_hour),
                minute=int(start_min),
                second=0,
                microsecond=0
            )
            
            end_datetime = current_date.replace(
                hour=int(end_hour),
                minute=int(end_min),
                second=0,
                microsecond=0
            )
            
            # 处理结束时间在第二天的情况
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
            
            events.append({
                'start': start_datetime.isoformat(),
                'end': end_datetime.isoformat(),
                'content': content.strip()
            })
    
    return events

def sync_to_notion(content, start_time=None, end_time=None):
    """将日志同步到Notion"""
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        print("缺少Notion API凭据，跳过同步")
        return None
    
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # 准备日期属性
    date_property = {}
    if start_time and end_time:
        date_property = {
            "start": start_time,
            "end": end_time
        }
    elif start_time:
        date_property = {
            "start": start_time
        }
    else:
        # 使用今天的日期
        today = datetime.now().strftime("%Y-%m-%d")
        date_property = {
            "start": today
        }
    
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "To-do": {
                "title": [
                    {
                        "text": {
                            "content": content
                        }
                    }
                ]
            },
            "Dates": {
                "date": date_property
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            print(f"向Notion同步时出错: {response.status_code}")
            print(response.text)
            return None
        
        return response.json().get('id')
    except Exception as e:
        print(f"向Notion同步时出错: {e}")
        return None