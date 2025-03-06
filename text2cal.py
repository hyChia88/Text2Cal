import re
from datetime import datetime, timedelta
from ics import Calendar, Event

def parse_input(text):
    """ 解析输入文本，先按日期拆分，再解析事件 """
    
    # 1. 拆分每一天的日程表
    day_schedules = [x.strip() for x in text.split("@") if x.strip()]
    
    all_events = {}

    # 2. 解析日期 & 事件
    for schedule in day_schedules:
        lines = schedule.split("\n")
        date_str = lines[0].strip()  # 获取日期
        event_lines = [line.strip() for line in lines[1:] if line.strip()]  # 过滤空行
        if event_lines:
            all_events[date_str] = event_lines

    parsed_events = []

    # 3. 解析每一天的事件
    event_pattern = r"-\s*(?P<start>\d{3,4}(am|pm))-(?P<end>\d{3,4}(am|pm))?\s*(?P<content>.+)"
    
    for date_str, event_list in all_events.items():
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%y").date()
        except ValueError:
            print(f"⚠️ 无效日期格式: {date_str}, 跳过该日期")
            continue
        
        for event_text in event_list:
            match = re.match(event_pattern, event_text)
            if not match:
                print(f"⚠️ 无法解析事件: {event_text}")
                continue
            
            start_time = match.group("start")
            end_time = match.group("end")
            content = match.group("content").strip()
            
            start_dt = datetime.strptime(start_time, "%I%M%p").time()
            
            if end_time:
                end_dt = datetime.strptime(end_time, "%I%M%p").time()
                if end_dt <= start_dt:
                    end_dt = (datetime.combine(date_obj, start_dt) + timedelta(hours=1)).time()
            else:
                end_dt = (datetime.combine(date_obj, start_dt) + timedelta(hours=1)).time()
            
            parsed_events.append({
                "date": date_obj,
                "start": start_dt,
                "end": end_dt,
                "content": content
            })
    
    return parsed_events

def generate_ics(events, filename="schedule.ics"):
    """ 生成 .ics 文件 """
    c = Calendar()
    
    for event in events:
        e = Event()
        start_datetime = datetime.combine(event["date"], event["start"])
        end_datetime = datetime.combine(event["date"], event["end"])
        e.name = event["content"]
        e.begin = start_datetime
        e.end = end_datetime
        c.events.add(e)
    
    with open(filename, "w") as f:
        f.writelines(c)  # Save .ics file
    print(f"✅ ICS 文件已生成: {filename}")

# 示例输入
text = """@03/04/25 
- 0930am-1030am Project Meeting
- 0200pm-0400pm Design Review

@15/05/25 
- 1000pm-0900am Overnight Hackathon

@21/06/25 
- 0300pm-0500pm Research Paper Review"""

# 解析并生成 .ics
parsed_events = parse_input(text)
generate_ics(parsed_events)
print(parsed_events)