import re
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import uuid


def generate_unique_id() -> str:
    """
    Generate a unique ID for logs and other entities.
    
    Returns:
        A unique string ID
    """
    return str(uuid.uuid4())


def clean_text(text: str) -> str:
    """
    Clean and normalize text for processing.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' URL ', text)
    
    # Replace email addresses
    text = re.sub(r'\S+@\S+', ' EMAIL ', text)
    
    # Normalize some common characters
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Remove special characters except for basic punctuation
    text = re.sub(r'[^\w\s.,!?;:\(\)\[\]\{\}\'"-]', ' ', text)
    
    # Remove multiple spaces again (after all replacements)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_log_date(log_content: str) -> Optional[datetime]:
    """
    Extract date information from log content.
    
    Args:
        log_content: The content of the log
        
    Returns:
        Extracted datetime or None if no date found
    """
    # Patterns for common date formats
    date_patterns = [
        # ISO format: 2023-03-15, 2023-03-15T10:30:00
        (r'(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?)', '%Y-%m-%d'),
        # American format: 03/15/2023, 3/15/2023
        (r'(\d{1,2}/\d{1,2}/\d{4})', '%m/%d/%Y'),
        # European format: 15/03/2023, 15/3/2023
        (r'(\d{1,2}/\d{1,2}/\d{4})', '%d/%m/%Y'),
        # Text format: March 15, 2023
        (r'([A-Za-z]+ \d{1,2}, \d{4})', '%B %d, %Y'),
        # Short text format: Mar 15, 2023
        (r'([A-Za-z]{3} \d{1,2}, \d{4})', '%b %d, %Y'),
    ]
    
    for pattern, date_format in date_patterns:
        match = re.search(pattern, log_content)
        if match:
            date_str = match.group(1)
            try:
                if 'T' in date_str:
                    return datetime.fromisoformat(date_str)
                else:
                    return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
    
    # No date found
    return None


def parse_date_time(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in various formats.
    
    Args:
        date_str: String containing a date
        
    Returns:
        Datetime object or None if parsing fails
    """
    formats = [
        '%Y-%m-%d',                 # ISO: 2023-03-15
        '%Y-%m-%dT%H:%M:%S',        # ISO with time: 2023-03-15T10:30:00
        '%Y-%m-%dT%H:%M:%S.%f',     # ISO with microseconds: 2023-03-15T10:30:00.000000
        '%m/%d/%Y',                 # US: 03/15/2023
        '%d/%m/%Y',                 # EU: 15/03/2023
        '%B %d, %Y',                # Long text: March 15, 2023
        '%b %d, %Y',                # Short text: Mar 15, 2023
        '%d %B %Y',                 # EU text: 15 March 2023
        '%d %b %Y',                 # EU short text: 15 Mar 2023
        '%Y%m%d',                   # Compact: 20230315
        '%m/%d/%Y %H:%M',           # US with time: 03/15/2023 10:30
        '%d/%m/%Y %H:%M',           # EU with time: 15/03/2023 10:30
        '%B %d, %Y %H:%M',          # Long text with time: March 15, 2023 10:30
        '%b %d, %Y %H:%M',          # Short text with time: Mar 15, 2023 10:30
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def calculate_date_difference(date1: datetime, date2: datetime) -> Dict[str, int]:
    """
    Calculate the difference between two dates in various units.
    
    Args:
        date1: First date
        date2: Second date
        
    Returns:
        Dictionary with differences in days, weeks, months, years
    """
    # Ensure date1 is before date2
    if date1 > date2:
        date1, date2 = date2, date1
    
    # Total difference in days
    delta = date2 - date1
    days_diff = delta.days
    
    # Calculate other units
    weeks_diff = days_diff // 7
    
    # Months and years are approximate
    months_diff = (date2.year - date1.year) * 12 + date2.month - date1.month
    years_diff = days_diff // 365
    
    return {
        'days': days_diff,
        'weeks': weeks_diff,
        'months': months_diff,
        'years': years_diff,
        'total_seconds': int(delta.total_seconds())
    }


def format_log_display(log: Dict[str, Any]) -> str:
    """
    Format a log entry for display.
    
    Args:
        log: The log dictionary
        
    Returns:
        Formatted log string
    """
    try:
        log_id = log.get('id', 'unknown')
        content = log.get('content', '')
        
        # Format timestamps
        start_time = None
        if 'start_time' in log:
            try:
                start_time = datetime.fromisoformat(log['start_time'])
            except (ValueError, TypeError):
                start_time = None
        
        end_time = None
        if 'end_time' in log and log['end_time']:
            try:
                end_time = datetime.fromisoformat(log['end_time'])
            except (ValueError, TypeError):
                end_time = None
        
        # Create time display string
        time_display = ""
        if start_time:
            if end_time:
                time_display = f"[{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}]"
            else:
                time_display = f"[{start_time.strftime('%Y-%m-%d %H:%M')}]"
        
        # Format importance if available
        importance_display = ""
        if 'importance' in log:
            importance = float(log['importance'])
            if importance >= 0.8:
                importance_display = "‼️ "  # High importance
            elif importance >= 0.5:
                importance_display = "❗ "  # Medium importance
        
        # Format log with time and content
        formatted_log = f"{importance_display}{time_display} {content}"
        
        # Add relevance score if available (for search results)
        if 'relevance_score' in log:
            relevance = float(log['relevance_score'])
            relevance_percent = int(relevance * 100)
            formatted_log += f" (Relevance: {relevance_percent}%)"
        
        return formatted_log.strip()
    
    except Exception as e:
        print(f"Error formatting log: {e}")
        return str(log)


def categorize_log(content: str) -> str:
    """
    Automatically categorize a log based on its content.
    
    Args:
        content: The log content
        
    Returns:
        Category name
    """
    # Convert to lowercase for case-insensitive matching
    content_lower = content.lower()
    
    # Define category patterns
    category_patterns = [
        (r'\bmeeting\b|\bconference\b|\bcall\b|\bdiscuss', 'Meeting'),
        (r'\btask\b|\btodo\b|\bassignment\b|\bcomplete', 'Task'),
        (r'\bidea\b|\bthought\b|\bconcept\b|\binspir', 'Idea'),
        (r'\bnote\b|\breminder\b|\bremember\b', 'Note'),
        (r'\bdecision\b|\bdecide\b|\bchoose\b|\bselect', 'Decision'),
        (r'\bproject\b|\binitiative\b|\bwork\b', 'Project'),
        (r'\bplan\b|\bschedule\b|\bcalendar\b|\bagenda', 'Planning'),
        (r'\bresearch\b|\bstudy\b|\binvestigate\b|\banalyz', 'Research'),
        (r'\bgoal\b|\bobjective\b|\btarget\b|\baim', 'Goal'),
        (r'\bfeedback\b|\breview\b|\bcomment\b|\bcritique', 'Feedback'),
    ]
    
    # Check each pattern
    for pattern, category in category_patterns:
        if re.search(pattern, content_lower):
            return category
    
    # Default category
    return 'General'


def extract_tags_from_content(content: str) -> List[str]:
    """
    Extract hashtags and mentioned entities from log content.
    
    Args:
        content: The log content
        
    Returns:
        List of extracted tags
    """
    # Extract hashtags (e.g., #project, #important)
    hashtags = re.findall(r'#(\w+)', content)
    
    # Extract @mentions (e.g., @john, @team)
    mentions = re.findall(r'@(\w+)', content)
    
    # Combine and return unique tags
    all_tags = hashtags + mentions
    return list(set(all_tags))


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity using Jaccard similarity.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    # Clean and tokenize texts
    tokens1 = set(clean_text(text1).split())
    tokens2 = set(clean_text(text2).split())
    
    # Handle empty sets
    if not tokens1 or not tokens2:
        return 0.0
    
    # Calculate Jaccard similarity: intersection / union
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union)


def format_time_ago(dt: datetime) -> str:
    """
    Format a datetime as a human-readable "time ago" string.
    
    Args:
        dt: Datetime to format
        
    Returns:
        String like "5 minutes ago", "2 hours ago", "3 days ago", etc.
    """
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{int(minutes)} minute{'s' if minutes != 1 else ''} ago"
    
    hours = minutes // 60
    if hours < 24:
        return f"{int(hours)} hour{'s' if hours != 1 else ''} ago"
    
    days = diff.days
    if days < 7:
        return f"{days} day{'s' if days != 1 else ''} ago"
    
    weeks = days // 7
    if weeks < 4:
        return f"{int(weeks)} week{'s' if weeks != 1 else ''} ago"
    
    months = days // 30
    if months < 12:
        return f"{int(months)} month{'s' if months != 1 else ''} ago"
    
    years = days // 365
    return f"{int(years)} year{'s' if years != 1 else ''} ago"


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        Dictionary with configuration settings
    """
    if not os.path.exists(config_path):
        # Return default config if file doesn't exist
        return {
            "api_keys": {},
            "storage": {
                "log_db_path": "logs.db",
                "uploads_dir": "uploads",
                "embeddings_dir": "embeddings"
            },
            "features": {
                "enable_notion_sync": False,
                "enable_openai_suggestions": False,
                "enable_image_analysis": False
            },
            "ui_preferences": {
                "theme": "light",
                "default_view": "timeline",
                "items_per_page": 20
            }
        }
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save the config file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def hash_content(content: str) -> str:
    """
    Create a hash of content for deduplication or verification.
    
    Args:
        content: The content to hash
        
    Returns:
        Hash string
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def get_log_importance(log: Dict[str, Any]) -> float:
    """
    Calculate the importance score of a log based on various factors.
    
    Args:
        log: The log dictionary
        
    Returns:
        Importance score between 0 and 1
    """
    # Start with base importance (default or user-defined)
    importance = log.get('importance', 0.5)
    
    # Increase importance based on content features
    content = log.get('content', '')
    
    # Check for importance indicators in content
    indicators = ['important', 'urgent', 'critical', 'priority', 'remember', 'deadline', 'key', 'crucial']
    for indicator in indicators:
        if re.search(rf'\b{indicator}\b', content, re.IGNORECASE):
            importance += 0.1
    
    # Check for exclamation marks
    exclamation_count = content.count('!')
    importance += min(exclamation_count * 0.05, 0.15)  # Max 0.15 bonus for exclamations
    
    # Check for uppercase words (emphasis)
    uppercase_words = re.findall(r'\b[A-Z]{2,}\b', content)
    importance += min(len(uppercase_words) * 0.05, 0.1)  # Max 0.1 bonus for uppercase
    
    # Cap importance at 1.0
    return min(importance, 1.0)


def filter_logs_by_timeframe(logs: List[Dict[str, Any]], days: int = 30) -> List[Dict[str, Any]]:
    """
    Filter logs to include only those within a specific timeframe.
    
    Args:
        logs: List of logs
        days: Number of days to include (from today)
        
    Returns:
        Filtered list of logs
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    filtered_logs = []
    for log in logs:
        try:
            log_date = datetime.fromisoformat(log.get('start_time', datetime.now().isoformat()))
            if log_date >= cutoff_date:
                filtered_logs.append(log)
        except (ValueError, TypeError):
            # Skip logs with invalid dates
            continue
    
    return filtered_logs