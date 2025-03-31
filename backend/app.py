from flask import Flask, request, jsonify
import json
from datetime import datetime, timedelta
from flask_cors import CORS
import os
import uuid

# Import project modules
from db_model import db
from notion_helper import sync_to_notion, parse_text
from openai_helper import OpenAIHelper
from memory_analyzer import MemoryAnalyzer
from memory_model import MemoryModel
from recommendation import MemoryRecommendationEngine
from file_processor import FileProcessor
from utils import (generate_unique_id, clean_text, extract_log_date, 
                  calculate_date_difference, format_log_display, categorize_log, 
                  extract_tags_from_content, filter_logs_by_timeframe)
from data_generator import DataGenerator

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize components
openai_helper = OpenAIHelper()
memory_model = MemoryModel()
memory_analyzer = MemoryAnalyzer(embedding_provider=memory_model.get_embedding)
recommendation_engine = MemoryRecommendationEngine(memory_analyzer, memory_model)
file_processor = FileProcessor(storage_dir="uploads")

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Routes for basic log management
@app.route("/api/add-log", methods=["POST"])
def add_log():
    """Add a new log entry."""
    data = request.get_json()
    log_text = data.get("log", "")
    
    if not log_text:
        return jsonify({"status": "error", "message": "Log text is required"}), 400
    
    # Try to parse structured format
    try:
        events = parse_text(log_text)
        log_ids = []
        
        if events:
            # Add parsed events
            for event in events:
                # Add to local database
                log_id = db.add_log(
                    content=event['content'],
                    start_time=event['start'],
                    end_time=event.get('end')
                )
                log_ids.append(log_id)
                
                # Sync to Notion if enabled
                try:
                    notion_id = sync_to_notion(
                        content=event['content'],
                        start_time=event['start'],
                        end_time=event.get('end')
                    )
                except Exception as e:
                    print(f"Error syncing to Notion: {e}")
            
            return jsonify({"status": "success", "log_ids": log_ids})
        
    except Exception as e:
        print(f"Error parsing events: {e}")
    
    # If no events or parsing failed, add as simple log
    # Extract date from content if available
    log_date = extract_log_date(log_text)
    start_time = log_date.isoformat() if log_date else datetime.now().isoformat()
    
    # Categorize log
    category = categorize_log(log_text)
    
    # Extract tags
    tags = extract_tags_from_content(log_text)
    
    # Add to database
    log_id = db.add_log(
        content=log_text,
        start_time=start_time,
        # category=category,
        tags=','.join(tags) if tags else None
    )
    
    # Sync to Notion if enabled
    try:
        notion_id = sync_to_notion(content=log_text, start_time=start_time)
    except Exception as e:
        print(f"Error syncing to Notion: {e}")
    
    return jsonify({"status": "success", "log_id": log_id})

@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Get logs with optional filtering."""
    # Get query parameters
    days = request.args.get('days', default=30, type=int)
    category = request.args.get('category', default=None, type=str)
    tag = request.args.get('tag', default=None, type=str)
    query = request.args.get('query', default=None, type=str)
    
    # Get logs from database
    logs = db.get_logs(days)
    
    # Apply additional filtering
    if category:
        logs = [log for log in logs if log.get('category') == category]
    
    if tag:
        logs = [log for log in logs if tag in (log.get('tags', '').split(',') if log.get('tags') else [])]
    
    if query:
        # Simple text search
        query = query.lower()
        logs = [log for log in logs if query in log.get('content', '').lower()]
    
    # Format logs for display
    formatted_logs = []
    for log in logs:
        start_time = datetime.fromisoformat(log['start_time'])
        
        # Format display time
        if log.get('end_time'):
            end_time = datetime.fromisoformat(log['end_time'])
            time_display = f"[{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}]"
        else:
            time_display = f"[{start_time.strftime('%Y-%m-%d %H:%M')}]"
        
        formatted_logs.append({
            "id": log['id'],
            "content": log['content'],
            "formatted": f"{time_display} {log['content']}",
            "start_time": log['start_time'],
            "end_time": log.get('end_time'),
            "category": log.get('category', 'General'),
            "tags": log.get('tags', '').split(',') if log.get('tags') else [],
            "importance": log.get('importance', 0.5)
        })
    
    return jsonify({"logs": formatted_logs})

@app.route("/api/logs/<log_id>", methods=["GET"])
def get_log(log_id):
    """Get a specific log by ID."""
    log = db.get_log(log_id)
    
    if not log:
        return jsonify({"status": "error", "message": "Log not found"}), 404
    
    # Format the log
    start_time = datetime.fromisoformat(log['start_time'])
    time_display = start_time.strftime('%Y-%m-%d %H:%M')
    
    formatted_log = {
        "id": log['id'],
        "content": log['content'],
        "formatted": f"[{time_display}] {log['content']}",
        "start_time": log['start_time'],
        "end_time": log.get('end_time'),
        "category": log.get('category', 'General'),
        "tags": log.get('tags', '').split(',') if log.get('tags') else [],
        "importance": log.get('importance', 0.5),
        "created_at": log.get('created_at')
    }
    
    return jsonify({"log": formatted_log})

@app.route("/api/logs/<log_id>", methods=["PUT"])
def update_log(log_id):
    """Update a log entry."""
    data = request.get_json()
    
    # Check if log exists
    log = db.get_log(log_id)
    if not log:
        return jsonify({"status": "error", "message": "Log not found"}), 404
    
    # Update fields
    updates = {}
    if 'content' in data:
        updates['content'] = data['content']
    
    if 'start_time' in data:
        updates['start_time'] = data['start_time']
    
    if 'end_time' in data:
        updates['end_time'] = data['end_time']
    
    if 'category' in data:
        updates['category'] = data['category']
    
    if 'tags' in data:
        if isinstance(data['tags'], list):
            updates['tags'] = ','.join(data['tags'])
        else:
            updates['tags'] = data['tags']
    
    if 'importance' in data:
        updates['importance'] = data['importance']
    
    # Perform the update
    success = db.update_log(log_id, **updates)
    
    if success:
        # Sync changes to Notion if enabled
        try:
            if 'content' in updates or 'start_time' in updates or 'end_time' in updates:
                sync_to_notion(
                    content=updates.get('content', log['content']),
                    start_time=updates.get('start_time', log['start_time']),
                    end_time=updates.get('end_time', log.get('end_time'))
                )
        except Exception as e:
            print(f"Error syncing updates to Notion: {e}")
        
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Failed to update log"}), 500

@app.route("/api/logs/<log_id>", methods=["DELETE"])
def delete_log(log_id):
    """Delete a log entry."""
    success = db.delete_log(log_id)
    
    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Log not found"}), 404

# Memory analysis and recommendation routes
@app.route("/api/analyze/logs", methods=["GET"])
def analyze_logs():
    """Analyze logs to find patterns and insights."""
    days = request.args.get('days', default=30, type=int)
    
    # Get logs
    logs = db.get_logs(days)
    
    if not logs:
        return jsonify({"message": "No logs found for analysis"}), 404
    
    # Generate insights using recommendation engine
    insights = recommendation_engine.generate_memory_insights(logs, timeframe_days=days)
    
    return jsonify({"insights": insights})

@app.route("/api/search", methods=["POST"])
def search_memories():
    """Search for memories based on content similarity."""
    data = request.get_json()
    query = data.get("query", "")
    max_results = data.get("max_results", 10)
    
    if not query:
        return jsonify({"status": "error", "message": "Query is required"}), 400
    
    # Get logs from database
    logs = db.get_logs(days=365)  # Search within past year
    
    if not logs:
        return jsonify({"results": [], "message": "No logs found for search"})
    
    # Generate recommendations based on query
    recommendations = recommendation_engine.get_recommendations(
        query=query,
        logs=logs,
        max_results=max_results
    )
    
    # Format the results
    results = []
    for rec in recommendations:
        # Format start time
        start_time = datetime.fromisoformat(rec.get('start_time', datetime.now().isoformat()))
        time_display = start_time.strftime('%Y-%m-%d %H:%M')
        
        results.append({
            "id": rec.get('id'),
            "content": rec.get('content', ''),
            "formatted": f"[{time_display}] {rec.get('content', '')}",
            "relevance_score": rec.get('relevance_score', 0),
            "start_time": rec.get('start_time'),
            "category": rec.get('category', 'General')
        })
    
    return jsonify({"results": results})

@app.route("/api/suggestion", methods=["GET"])
def get_suggestion():
    """Generate suggestions based on recent logs."""
    days = request.args.get('days', default=7, type=int)
    language = request.args.get('language', default='en', type=str)
    
    # Get recent logs
    recent_logs = db.get_logs(days)
    
    if not recent_logs:
        if language == 'zh':
            message = "没有找到最近的日志记录，无法生成建议。请添加一些日志，然后再试一次。"
        else:
            message = "No recent logs found. Please add some logs and try again."
        return jsonify({"suggestion": message})
    
    # Generate suggestion using OpenAI helper
    try:
        suggestion_text = openai_helper.generate_suggestion(recent_logs, language)
        return jsonify({"suggestion": suggestion_text})
    except Exception as e:
        print(f"Error generating suggestion: {e}")
        if language == 'zh':
            message = f"生成建议时遇到错误: {str(e)}"
        else:
            message = f"Error generating suggestion: {str(e)}"
        return jsonify({"suggestion": message})

@app.route("/api/connections/<log_id>", methods=["GET"])
def get_log_connections(log_id):
    """Get connections between a log and other logs."""
    # Get the target log
    target_log = db.get_log(log_id)
    
    if not target_log:
        return jsonify({"status": "error", "message": "Log not found"}), 404
    
    # Get other logs (excluding the target log)
    all_logs = db.get_logs(days=90)  # Get logs from past 90 days
    other_logs = [log for log in all_logs if log['id'] != log_id]
    
    if not other_logs:
        return jsonify({"connections": [], "message": "No other logs found for comparison"})
    
    # Find connections using memory analyzer
    connections = []
    
    # 1. Find temporal connections
    temporal_connections = memory_analyzer.generate_temporal_connections([target_log] + other_logs)
    temporal_connected_ids = temporal_connections.get(log_id, [])
    
    # 2. Find semantic connections using memory model
    log_embeddings = {}
    target_embedding = None
    
    try:
        # Generate embeddings for target log
        target_embedding = memory_model.get_embedding(target_log['content'])
        
        # Generate embeddings for other logs
        for log in other_logs:
            log_embeddings[log['id']] = memory_model.get_embedding(log['content'])
        
        # Find similar logs
        similar_logs = memory_model.find_similar_logs(
            target_embedding, 
            log_embeddings, 
            top_k=5
        )
        
        # Add semantic connections
        for log_id, similarity in similar_logs:
            if similarity > 0.5:  # Only include reasonably similar logs
                connected_log = next((log for log in other_logs if log['id'] == log_id), None)
                if connected_log:
                    connections.append({
                        "log": connected_log,
                        "connection_type": "Semantic Similarity",
                        "explanation": "Content similarity based on semantic analysis",
                        "similarity_score": similarity
                    })
    except Exception as e:
        print(f"Error finding semantic connections: {e}")
    
    # 3. Add temporal connections that aren't already included
    for log_id in temporal_connected_ids:
        # Check if this log is already in connections
        if not any(c['log'].get('id') == log_id for c in connections):
            connected_log = next((log for log in other_logs if log['id'] == log_id), None)
            if connected_log:
                connections.append({
                    "log": connected_log,
                    "connection_type": "Temporal Proximity",
                    "explanation": "Logs created around the same time",
                    "similarity_score": 0.7  # Default score for temporal connections
                })
    
    # Format the connections for response
    formatted_connections = []
    for connection in connections:
        log = connection['log']
        formatted_connections.append({
            "id": log['id'],
            "content": log['content'],
            "start_time": log['start_time'],
            "connection_type": connection['connection_type'],
            "explanation": connection['explanation'],
            "similarity_score": connection['similarity_score']
        })
    
    return jsonify({"connections": formatted_connections})

# File handling routes
@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload a file and extract information from it."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    try:
        # Save the file
        file_data = file.read()
        file_path = file_processor.save_file(file_data, file.filename)
        
        # Get file metadata
        metadata = file_processor.get_file_metadata(file_path)
        
        # Extract text content if possible
        text_content = file_processor.extract_text_from_file(file_path)
        
        # Generate a summary of the file
        summary = ""
        if text_content:
            try:
                summary = openai_helper.generate_log_summary([{"content": text_content}], max_length=200)
            except Exception as e:
                print(f"Error generating file summary: {e}")
                summary = "Could not generate summary"
        
        # Create a log entry for the file
        log_content = f"File uploaded: {file.filename}"
        if summary:
            log_content += f"\nSummary: {summary}"
        
        log_id = db.add_log(
            content=log_content,
            start_time=datetime.now().isoformat(),
            category="File",
            metadata=json.dumps({
                "file_path": file_path,
                "file_type": metadata.get("file_type", ""),
                "file_size": metadata.get("size_bytes", 0),
                "has_text": bool(text_content)
            })
        )
        
        return jsonify({
            "status": "success",
            "file_path": file_path,
            "metadata": metadata,
            "summary": summary,
            "log_id": log_id
        })
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/files/<log_id>/analyze", methods=["GET"])
def analyze_file(log_id):
    """Analyze a file associated with a log."""
    # Get the log
    log = db.get_log(log_id)
    
    if not log:
        return jsonify({"status": "error", "message": "Log not found"}), 404
    
    # Check if this is a file log
    if log.get('category') != "File":
        return jsonify({"status": "error", "message": "This log is not associated with a file"}), 400
    
    # Extract file path from metadata
    try:
        metadata = json.loads(log.get('metadata', '{}'))
        file_path = metadata.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File not found"}), 404
        
        # Determine file type
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Analyze based on file type
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            # Image analysis
            try:
                # Get sensory descriptions
                sensory_descriptions = openai_helper.get_sensory_descriptions(file_path)
                
                # Get content analysis
                content_analysis = openai_helper.analyze_image_content(file_path)
                
                return jsonify({
                    "status": "success",
                    "file_type": "image",
                    "sensory_descriptions": sensory_descriptions,
                    "content_analysis": content_analysis
                })
            except Exception as e:
                print(f"Error analyzing image: {e}")
                return jsonify({"status": "error", "message": f"Error analyzing image: {str(e)}"}), 500
        
        elif file_ext in ['.pdf', '.docx', '.doc', '.txt']:
            # Text document analysis
            try:
                # Extract text
                text_content = file_processor.extract_text_from_file(file_path)
                
                # Generate a summary
                summary = openai_helper.generate_log_summary([{"content": text_content}], max_length=300)
                
                # Analyze emotional tone
                emotion_analysis = openai_helper.analyze_log_emotion(text_content[:1000])  # Limit to first 1000 chars
                
                return jsonify({
                    "status": "success",
                    "file_type": "document",
                    "summary": summary,
                    "emotion_analysis": emotion_analysis,
                    "text_length": len(text_content),
                    "text_preview": text_content[:500] + "..." if len(text_content) > 500 else text_content
                })
            except Exception as e:
                print(f"Error analyzing document: {e}")
                return jsonify({"status": "error", "message": f"Error analyzing document: {str(e)}"}), 500
        
        else:
            # Generic file analysis
            file_summary = file_processor.get_file_summary(file_path)
            return jsonify({
                "status": "success",
                "file_type": "other",
                "file_summary": file_summary
            })
        
    except Exception as e:
        print(f"Error processing file analysis: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Stats and dashboard routes
@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get statistics about logs and usage."""
    days = request.args.get('days', default=30, type=int)
    
    # Get logs
    logs = db.get_logs(days)
    
    if not logs:
        return jsonify({
            "total_logs": 0,
            "logs_by_category": {},
            "logs_by_day": {},
            "logs_by_hour": {}
        })
    
    # Calculate basic stats
    total_logs = len(logs)
    
    # Group by category
    logs_by_category = {}
    for log in logs:
        category = log.get('category', 'General')
        logs_by_category[category] = logs_by_category.get(category, 0) + 1
    
    # Group by day
    logs_by_day = {}
    for log in logs:
        dt = datetime.fromisoformat(log['start_time'])
        day = dt.strftime('%Y-%m-%d')
        logs_by_day[day] = logs_by_day.get(day, 0) + 1
    
    # Group by hour
    logs_by_hour = {}
    for log in logs:
        dt = datetime.fromisoformat(log['start_time'])
        hour = dt.hour
        logs_by_hour[hour] = logs_by_hour.get(hour, 0) + 1
    
    # Most active days
    most_active_days = sorted(logs_by_day.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Most active hours
    most_active_hours = sorted(logs_by_hour.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        "total_logs": total_logs,
        "logs_by_category": logs_by_category,
        "logs_by_day": logs_by_day,
        "logs_by_hour": logs_by_hour,
        "most_active_days": most_active_days,
        "most_active_hours": most_active_hours
    })

@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Get all log categories."""
    logs = db.get_logs(days=365)  # Get all logs from past year
    
    categories = set()
    for log in logs:
        category = log.get('category')
        if category:
            categories.add(category)
    
    return jsonify({"categories": list(categories)})

@app.route("/api/tags", methods=["GET"])
def get_tags():
    """Get all tags used in logs."""
    logs = db.get_logs(days=365)  # Get all logs from past year
    
    all_tags = set()
    for log in logs:
        tags_str = log.get('tags', '')
        if tags_str:
            tags = tags_str.split(',')
            all_tags.update(tags)
    
    # Sort tags alphabetically
    sorted_tags = sorted(list(all_tags))
    
    return jsonify({"tags": sorted_tags})

# 添加生成合成数据的路由
@app.route("/api/generate-synthetic-data", methods=["POST"])
def generate_synthetic_data():
    """Generate synthetic data and load to database"""
    data = request.get_json()
    num_samples = data.get("num_samples", 100)
    use_enhanced = data.get("use_enhanced", True)  # Add this parameter
    openai_ratio = data.get("openai_ratio", 0.3)   # Add this parameter
    
    try:
        # Pass the enhancement options to the DataGenerator
        generator = DataGenerator(use_enhanced=use_enhanced)
        count = generator.generate_and_load_to_db(db, num_samples, openai_ratio)
        
        return jsonify({
            "status": "success", 
            "message": f"Generated {count} synthetic memory records",
            "count": count,
            "enhanced": use_enhanced
        })
    except Exception as e:
        print(f"Error generating synthetic data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 添加获取记忆嵌入的路由
@app.route("/api/get-embeddings", methods=["POST"])
def get_embeddings():
    """获取记忆内容的嵌入向量"""
    data = request.get_json()
    texts = data.get("texts", [])
    
    if not texts:
        return jsonify({"status": "error", "message": "No texts provided"}), 400
    
    try:
        # 使用 OpenAI 获取嵌入
        embeddings = []
        # 批量处理，每次最多16个文本
        for i in range(0, len(texts), 16):
            batch = texts[i:i+16]
            batch_embeddings = openai_helper.generate_embeddings(batch)
            embeddings.extend(batch_embeddings)
        
        return jsonify({
            "status": "success",
            "embeddings": embeddings
        })
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 添加记忆内容填充生成的路由
@app.route("/api/generate-memory-completion", methods=["POST"])
def generate_memory_completion():
    """Generate memory completion based on weighted memories"""
    data = request.get_json()
    memory_ids = data.get("memory_ids", [])
    weights = data.get("weights", {})
    
    if not memory_ids:
        return jsonify({"status": "error", "message": "No memory IDs provided"}), 400
    
    try:
        # Get memory content
        memories = []
        for memory_id in memory_ids:
            memory = db.get_log(memory_id)
            if memory:
                memories.append(memory)
        
        if not memories:
            return jsonify({"status": "error", "message": "No valid memories found"}), 404
        
        # Generate completion
        completion_result = openai_helper.generate_memory_completion(memories, weights)
        
        return jsonify({
            "status": "success",
            "completion": completion_result.get("completion", ""),
            "original_contents": completion_result.get("original_contents", []),
            "original_count": len(memories)
        })
    except Exception as e:
        print(f"Error generating memory completion: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Main entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)