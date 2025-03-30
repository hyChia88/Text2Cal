import numpy as np
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any, Tuple, Optional

class MemoryAnalyzer:
    """
    Handles the analysis of user logs and creates semantic connections between memories.
    This class is responsible for extracting patterns, computing relevance, and identifying
    related logs based on content similarity and temporal proximity.
    """
    
    def __init__(self, embedding_provider=None):
        """
        Initialize the MemoryAnalyzer.
        
        Args:
            embedding_provider: A function or object that provides embeddings for text content.
                               If None, simple TF-IDF based similarity will be used.
        """
        self.embedding_provider = embedding_provider
        # Default weights for different factors when calculating memory relevance
        self.relevance_weights = {
            'recency': 0.3,      # How recent the memory is
            'frequency': 0.2,    # How frequently the memory has been accessed
            'similarity': 0.4,   # Content similarity to current context
            'importance': 0.1,   # User-defined or auto-calculated importance
        }
    
    def extract_entities(self, log_content: str) -> List[str]:
        """
        Extract important entities from log content (e.g., people, locations, projects).
        
        Args:
            log_content: The text content of the log.
            
        Returns:
            A list of extracted entities.
        """
        # Simple regex-based entity extraction (can be replaced with NER model)
        entities = []
        
        # Extract potential people names (capitalized words)
        name_pattern = r'\b[A-Z][a-z]+ (?:[A-Z][a-z]+\s?)+\b'
        names = re.findall(name_pattern, log_content)
        entities.extend(names)
        
        # Extract potential locations (words after "at", "in", "to")
        location_pattern = r'\b(?:at|in|to) ([A-Z][a-z]+ (?:[A-Z][a-z]+\s?)*)\b'
        locations = re.findall(location_pattern, log_content)
        entities.extend(locations)
        
        # Extract potential project names (words after "project", "working on")
        project_pattern = r'\b(?:project|working on) "([^"]+)"\b'
        projects = re.findall(project_pattern, log_content)
        entities.extend(projects)
        
        return list(set(entities))  # Remove duplicates
    
    def compute_recency_score(self, log_date: datetime, current_date: Optional[datetime] = None) -> float:
        """
        Compute a score based on how recent the log is.
        
        Args:
            log_date: The creation date of the log.
            current_date: The date to compare against (defaults to now).
            
        Returns:
            A score between 0 and 1, where 1 is very recent.
        """
        if current_date is None:
            current_date = datetime.now()
        
        # Calculate days difference
        days_diff = (current_date - log_date).days
        
        # Exponential decay function: score = e^(-days_diff/30)
        # This gives a score of 1 for today, ~0.7 for a week ago, 
        # ~0.37 for a month ago, and close to 0 for very old logs
        score = np.exp(-days_diff / 30)
        
        return min(max(score, 0), 1)  # Ensure score is between 0 and 1
    
    def compute_similarity_score(self, log_content: str, query_content: str) -> float:
        """
        Compute a similarity score between a log and a query.
        
        Args:
            log_content: The content of the log.
            query_content: The query to compare against.
            
        Returns:
            A similarity score between 0 and 1.
        """
        # If embedding provider is available, use it for similarity calculation
        if self.embedding_provider:
            try:
                log_embedding = self.embedding_provider(log_content)
                query_embedding = self.embedding_provider(query_content)
                
                # Compute cosine similarity
                similarity = np.dot(log_embedding, query_embedding) / (
                    np.linalg.norm(log_embedding) * np.linalg.norm(query_embedding)
                )
                return float(similarity)
            except Exception as e:
                print(f"Error computing embeddings: {e}")
        
        # Fallback to simple word overlap ratio
        log_words = set(log_content.lower().split())
        query_words = set(query_content.lower().split())
        
        if not log_words or not query_words:
            return 0.0
        
        # Jaccard similarity: intersection over union
        intersection = len(log_words.intersection(query_words))
        union = len(log_words.union(query_words))
        
        return intersection / union if union > 0 else 0.0
    
    def compute_memory_relevance(
        self, 
        log: Dict[str, Any], 
        query: str, 
        logs_access_frequency: Dict[str, int],
        current_date: Optional[datetime] = None
    ) -> float:
        """
        Compute the overall relevance of a log to the current query/context.
        
        Args:
            log: The log dictionary with content, date, etc.
            query: The current query or context.
            logs_access_frequency: Dictionary mapping log IDs to their access counts.
            current_date: The date to use for recency calculation.
            
        Returns:
            A relevance score between 0 and 1.
        """
        log_id = log.get('id')
        log_content = log.get('content', '')
        log_date = datetime.fromisoformat(log.get('start_time', datetime.now().isoformat()))
        log_importance = log.get('importance', 0.5)  # Default to middle importance
        
        # Compute individual scores
        recency_score = self.compute_recency_score(log_date, current_date)
        similarity_score = self.compute_similarity_score(log_content, query)
        
        # Compute frequency score based on access count
        max_access = max(logs_access_frequency.values()) if logs_access_frequency else 1
        frequency_score = logs_access_frequency.get(log_id, 0) / max_access if max_access > 0 else 0
        
        # Combine scores using weights
        relevance = (
            self.relevance_weights['recency'] * recency_score +
            self.relevance_weights['similarity'] * similarity_score +
            self.relevance_weights['frequency'] * frequency_score +
            self.relevance_weights['importance'] * log_importance
        )
        
        return min(max(relevance, 0), 1)  # Ensure score is between 0 and 1
    
    def find_related_memories(
        self, 
        logs: List[Dict[str, Any]], 
        query: str, 
        logs_access_frequency: Dict[str, int],
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the most relevant logs for a given query.
        
        Args:
            logs: A list of logs to search through.
            query: The query to find relevant logs for.
            logs_access_frequency: Dictionary mapping log IDs to their access counts.
            max_results: Maximum number of results to return.
            
        Returns:
            A list of relevant logs with their relevance scores.
        """
        if not logs:
            return []
        
        # Compute relevance for each log
        results = []
        for log in logs:
            relevance = self.compute_memory_relevance(log, query, logs_access_frequency)
            log_with_relevance = log.copy()
            log_with_relevance['relevance'] = relevance
            results.append(log_with_relevance)
        
        # Sort by relevance (descending) and return top results
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:max_results]
    
    def identify_patterns(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify patterns in user logs, such as recurring activities, time patterns, etc.
        
        Args:
            logs: A list of logs to analyze.
            
        Returns:
            A dictionary of identified patterns.
        """
        if not logs:
            return {}
        
        patterns = {
            'time_of_day': {},    # When the user tends to log entries
            'weekday_activity': {},  # Activity patterns by day of week
            'recurring_topics': [],  # Common topics/themes
            'entity_frequency': {}   # Frequency of mentioned entities
        }
        
        # Process each log
        for log in logs:
            content = log.get('content', '')
            log_date = datetime.fromisoformat(log.get('start_time', datetime.now().isoformat()))
            
            # Analyze time of day
            hour = log_date.hour
            time_category = 'morning' if 5 <= hour < 12 else 'afternoon' if 12 <= hour < 17 else 'evening' if 17 <= hour < 21 else 'night'
            patterns['time_of_day'][time_category] = patterns['time_of_day'].get(time_category, 0) + 1
            
            # Analyze weekday
            weekday = log_date.strftime('%A')
            patterns['weekday_activity'][weekday] = patterns['weekday_activity'].get(weekday, 0) + 1
            
            # Extract entities
            entities = self.extract_entities(content)
            for entity in entities:
                patterns['entity_frequency'][entity] = patterns['entity_frequency'].get(entity, 0) + 1
        
        # Extract most common entities
        top_entities = sorted(patterns['entity_frequency'].items(), key=lambda x: x[1], reverse=True)[:10]
        patterns['top_entities'] = [entity for entity, count in top_entities]
        
        # Normalize frequencies to percentages
        total_logs = len(logs)
        for key in ['time_of_day', 'weekday_activity']:
            for subkey in patterns[key]:
                patterns[key][subkey] = patterns[key][subkey] / total_logs * 100
        
        return patterns
    
    def generate_temporal_connections(self, logs: List[Dict[str, Any]], time_window_days: int = 3) -> Dict[str, List[str]]:
        """
        Generate connections between logs based on temporal proximity.
        
        Args:
            logs: A list of logs to analyze.
            time_window_days: The maximum number of days between logs to consider them connected.
            
        Returns:
            A dictionary mapping log IDs to lists of connected log IDs.
        """
        if not logs:
            return {}
        
        connections = {}
        
        # Sort logs by date
        sorted_logs = sorted(logs, key=lambda x: x.get('start_time', ''))
        
        for i, log in enumerate(sorted_logs):
            log_id = log.get('id')
            log_date = datetime.fromisoformat(log.get('start_time', datetime.now().isoformat()))
            connections[log_id] = []
            
            # Look backward for temporal connections
            for j in range(i-1, -1, -1):
                prev_log = sorted_logs[j]
                prev_log_id = prev_log.get('id')
                prev_log_date = datetime.fromisoformat(prev_log.get('start_time', datetime.now().isoformat()))
                
                # Check if logs are within the time window
                if (log_date - prev_log_date).days <= time_window_days:
                    connections[log_id].append(prev_log_id)
                else:
                    # If we've gone beyond the time window, stop checking earlier logs
                    break
            
            # Look forward for temporal connections
            for j in range(i+1, len(sorted_logs)):
                next_log = sorted_logs[j]
                next_log_id = next_log.get('id')
                next_log_date = datetime.fromisoformat(next_log.get('start_time', datetime.now().isoformat()))
                
                # Check if logs are within the time window
                if (next_log_date - log_date).days <= time_window_days:
                    connections[log_id].append(next_log_id)
                else:
                    # If we've gone beyond the time window, stop checking later logs
                    break
        
        return connections
    
    def update_relevance_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Update the weights used for computing memory relevance.
        
        Args:
            new_weights: Dictionary of new weights.
        """
        # Validate weights
        for key in new_weights:
            if key not in self.relevance_weights:
                raise ValueError(f"Invalid weight key: {key}")
        
        # Update weights
        self.relevance_weights.update(new_weights)
        
        # Normalize weights to sum to 1
        total_weight = sum(self.relevance_weights.values())
        if total_weight > 0:
            for key in self.relevance_weights:
                self.relevance_weights[key] /= total_weight