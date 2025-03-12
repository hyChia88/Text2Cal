import requests
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def parse_text(text):
    """
    解析文本输入，支持多种格式:
    1. @dd/mm/yyyy start_time-end_time: [To-do]
    2. @dd/mm/yy start_time-end_time: [To-do]
    
    可以输入多个同一日期的事件:
    @dd/mm/yy start_time-end_time: [To-do]
    start_time-end_time: [To-do]
    start_time-end_time: [To-do]
    
    返回包含'start'、'end'和'content'键的事件字典列表
    """
    lines = text.strip().split('\n')
    events = []
    current_date = None
    
    # 支持多种日期格式
    date_patterns = [
        r'@(\d{1,2}/\d{1,2}/\d{2,4})',  # @dd/mm/yy 或 @dd/mm/yyyy
        r'@(\d{1,2}-\d{1,2}-\d{2,4})',   # @dd-mm-yy 或 @dd-mm-yyyy
        r'@(\d{4}-\d{1,2}-\d{1,2})'      # @yyyy-mm-dd
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检查这行是否指定了新日期
        date_found = False
        for pattern in date_patterns:
            date_match = re.search(pattern, line)
            if date_match:
                date_str = date_match.group(1)
                try:
                    # 解析日期，支持多种格式
                    formats = ["%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y", "%Y-%m-%d"]
                    for fmt in formats:
                        try:
                            current_date = datetime.strptime(date_str, fmt)
                            date_found = True
                            break
                        except ValueError:
                            continue
                    
                    if not date_found:
                        print(f"无法解析日期格式: {date_str}，使用今天的日期。")
                        current_date = datetime.now()
                except Exception as e:
                    print(f"日期解析错误: {e}. 使用今天的日期。")
                    current_date = datetime.now()
                break
        
        # 如果行中没有找到日期且没有之前的日期，则使用今天
        if current_date is None:
            current_date = datetime.now()
        
        # 提取时间和内容，支持多种格式
        time_format_found = False
        
        # 格式1: 3:30pm-5pm: Webapp class
        pattern1 = r'(\d{1,2}):?(\d{2})?(?:am|pm)?-(\d{1,2}):?(\d{2})?(?:am|pm)?:\s*(.+)'
        match1 = re.search(pattern1, line)
        if match1:
            time_format_found = True
            start_hour = int(match1.group(1))
            start_min = int(match1.group(2) or "0")
            end_hour = int(match1.group(3))
            end_min = int(match1.group(4) or "0")
            content = match1.group(5).strip()
            
            # 处理AM/PM
            if "pm" in line.lower() and start_hour < 12:
                start_hour += 12
            if "pm" in line.lower() and end_hour < 12:
                end_hour += 12
        
        # 格式2: 6pm-8pm Dating (无冒号)
        if not time_format_found:
            pattern2 = r'(\d{1,2}):?(\d{2})?(?:am|pm)?-(\d{1,2}):?(\d{2})?(?:am|pm)\s+(.+)'
            match2 = re.search(pattern2, line)
            if match2:
                time_format_found = True
                start_hour = int(match2.group(1))
                start_min = int(match2.group(2) or "0")
                end_hour = int(match2.group(3))
                end_min = int(match2.group(4) or "0")
                content = match2.group(5).strip()
                
                # 处理AM/PM
                if "pm" in line.lower() and start_hour < 12:
                    start_hour += 12
                if "pm" in line.lower() and end_hour < 12:
                    end_hour += 12
        
        # 如果找到了时间格式，创建事件
        if time_format_found:
            start_datetime = current_date.replace(
                hour=start_hour,
                minute=start_min,
                second=0,
                microsecond=0
            )
            
            end_datetime = current_date.replace(
                hour=end_hour,
                minute=end_min,
                second=0,
                microsecond=0
            )
            
            # 处理结束时间在第二天的情况
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
            
            events.append({
                'start': start_datetime.isoformat(),
                'end': end_datetime.isoformat(),
                'content': content
            })
        # 如果没有找到时间格式但有日期，将整行作为内容
        elif date_found:
            content_match = re.search(r'@\S+\s+(.*)', line)
            if content_match:
                content = content_match.group(1).strip()
                if content:
                    events.append({
                        'start': current_date.isoformat(),
                        'end': None,
                        'content': content
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