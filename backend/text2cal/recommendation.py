import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import json
import re
from collections import Counter

from memory_analyzer import MemoryAnalyzer
from memory_model import MemoryModel


class MemoryRecommendationEngine:
    """
    Handles memory recommendations and insight generation based on user logs.
    Implements various recommendation strategies and generates personalized insights.
    """
    
    def __init__(self, memory_analyzer: Optional[MemoryAnalyzer] = None, 
                 memory_model: Optional[MemoryModel] = None):
        """
        Initialize the recommendation engine.
        
        Args:
            memory_analyzer: MemoryAnalyzer instance
            memory_model: MemoryModel instance
        """
        self.memory_analyzer = memory_analyzer or MemoryAnalyzer()
        self.memory_model = memory_model or MemoryModel()
        
        # Default weights for different recommendation strategies
        self.strategy_weights = {
            'content_similarity': 0.5,  # Weight for content-based recommendations
            'temporal_relevance': 0.3,  # Weight for time-based recommendations
            'user_behavior': 0.2,      # Weight for user interaction patterns
        }
    
    def get_recommendations(self, 
                           query: str, 
                           logs: List[Dict[str, Any]], 
                           user_preferences: Optional[Dict[str, Any]] = None,
                           max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Get memory recommendations based on a query and user context.
        
        Args:
            query: The search query or current context
            logs: List of user logs to search through
            user_preferences: Optional user preferences for personalization
            max_results: Maximum number of recommendations to return
            
        Returns:
            List of recommended memory logs with relevance scores
        """
        if not logs:
            return []
        
        # Apply user preferences if available
        if user_preferences:
            self._apply_user_preferences(user_preferences)
        
        # Get access frequency data (mock implementation - should come from user behavior tracking)
        logs_access_frequency = self._get_logs_access_frequency(logs)
        
        # Generate recommendations using different strategies
        content_recs = self._get_content_based_recommendations(query, logs, logs_access_frequency)
        temporal_recs = self._get_temporal_recommendations(query, logs)
        behavior_recs = self._get_behavior_based_recommendations(query, logs, logs_access_frequency)
        
        # Combine recommendations with weighted scores
        combined_scores = {}
        for log_id, score in content_recs:
            combined_scores[log_id] = self.strategy_weights['content_similarity'] * score
            
        for log_id, score in temporal_recs:
            if log_id in combined_scores:
                combined_scores[log_id] += self.strategy_weights['temporal_relevance'] * score
            else:
                combined_scores[log_id] = self.strategy_weights['temporal_relevance'] * score
                
        for log_id, score in behavior_recs:
            if log_id in combined_scores:
                combined_scores[log_id] += self.strategy_weights['user_behavior'] * score
            else:
                combined_scores[log_id] = self.strategy_weights['user_behavior'] * score
        
        # Sort by combined score and get top results
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        top_log_ids = [log_id for log_id, _ in sorted_results[:max_results]]
        
        # Construct result objects with full log details
        results = []
        for log_id in top_log_ids:
            log = next((l for l in logs if l.get('id') == log_id), None)
            if log:
                result = log.copy()
                result['relevance_score'] = combined_scores[log_id]
                results.append(result)
        
        return results
    
    def _apply_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Apply user preferences to the recommendation engine.
        
        Args:
            preferences: User preference settings
        """
        # Update strategy weights if provided
        if 'strategy_weights' in preferences:
            for strategy, weight in preferences['strategy_weights'].items():
                if strategy in self.strategy_weights:
                    self.strategy_weights[strategy] = weight
            
            # Normalize weights to sum to 1
            total_weight = sum(self.strategy_weights.values())
            if total_weight > 0:
                for strategy in self.strategy_weights:
                    self.strategy_weights[strategy] /= total_weight
        
        # Update memory analyzer relevance weights if provided
        if 'relevance_weights' in preferences and hasattr(self.memory_analyzer, 'update_relevance_weights'):
            self.memory_analyzer.update_relevance_weights(preferences['relevance_weights'])
    
    def _get_logs_access_frequency(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get access frequency for logs (should be replaced with actual usage tracking).
        
        Args:
            logs: List of logs
            
        Returns:
            Dictionary mapping log IDs to access counts
        """
        # This is a mock implementation. In a real system, this data would come from
        # a database tracking user interactions with logs.
        access_frequency = {}
        for log in logs:
            log_id = log.get('id')
            if log_id:
                # Mock frequency based on log age (newer logs accessed more)
                days_old = (datetime.now() - datetime.fromisoformat(log.get('start_time', datetime.now().isoformat()))).days
                # Randomize a bit to simulate real usage patterns
                frequency = max(0, 10 - int(days_old / 7)) + np.random.randint(0, 3)
                access_frequency[log_id] = frequency
        
        return access_frequency
    
    def _get_content_based_recommendations(self, 
                                         query: str, 
                                         logs: List[Dict[str, Any]],
                                         logs_access_frequency: Dict[str, int]) -> List[Tuple[str, float]]:
        """
        Get recommendations based on content similarity.
        
        Args:
            query: Search query or context
            logs: List of logs
            logs_access_frequency: Dictionary mapping log IDs to access counts
            
        Returns:
            List of (log_id, score) tuples
        """
        # Use the memory analyzer to find related memories
        related_memories = self.memory_analyzer.find_related_memories(
            logs, query, logs_access_frequency, max_results=len(logs)
        )
        
        # Extract log IDs and relevance scores
        recommendations = []
        for memory in related_memories:
            log_id = memory.get('id')
            relevance = memory.get('relevance', 0.0)
            if log_id:
                recommendations.append((log_id, relevance))
        
        return recommendations
    
    def _get_temporal_recommendations(self, 
                                     query: str, 
                                     logs: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
        """
        Get recommendations based on temporal patterns.
        
        Args:
            query: Search query or context
            logs: List of logs
            
        Returns:
            List of (log_id, score) tuples
        """
        # Extract date/time references from query
        now = datetime.now()
        date_references = self._extract_date_references(query, now)
        
        # If no explicit date references, default to recent logs
        if not date_references:
            date_references = [(now, 1.0)]
        
        # Score logs based on temporal proximity to referenced dates
        scores = {}
        for log in logs:
            log_id = log.get('id')
            if not log_id:
                continue
                
            log_time = datetime.fromisoformat(log.get('start_time', now.isoformat()))
            
            # Calculate temporal score for each referenced date
            for ref_date, ref_weight in date_references:
                # Calculate days difference
                days_diff = abs((ref_date - log_time).days)
                
                # Score using exponential decay function
                time_score = np.exp(-days_diff / 7) * ref_weight  # 7-day half-life
                
                # Update score (use max if multiple date references match)
                if log_id in scores:
                    scores[log_id] = max(scores[log_id], time_score)
                else:
                    scores[log_id] = time_score
        
        # Convert to list of tuples and sort
        recommendations = [(log_id, score) for log_id, score in scores.items()]
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations
    
    def _extract_date_references(self, query: str, reference_date: datetime) -> List[Tuple[datetime, float]]:
        """
        Extract date references from a query.
        
        Args:
            query: Text query
            reference_date: Reference date for relative time expressions
            
        Returns:
            List of (datetime, weight) tuples
        """
        date_references = []
        
        # Extract explicit date mentions
        # Example patterns: "March 15", "2023-04-20", "last week", "yesterday", etc.
        date_patterns = [
            # Absolute dates (e.g., "March 15, 2023", "2023-04-20")
            (r'\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b', lambda m: self._parse_date_match(m, reference_date)),
            (r'\b(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{2,4})?\b', lambda m: self._parse_month_day_match(m, reference_date)),
            
            # Relative dates
            (r'\byesterday\b', lambda m: (reference_date - timedelta(days=1), 1.0)),
            (r'\btoday\b', lambda m: (reference_date, 1.0)),
            (r'\btomorrow\b', lambda m: (reference_date + timedelta(days=1), 1.0)),
            (r'\blast\s+week\b', lambda m: (reference_date - timedelta(weeks=1), 0.8)),
            (r'\blast\s+month\b', lambda m: (reference_date - timedelta(days=30), 0.7)),
            (r'\bnext\s+week\b', lambda m: (reference_date + timedelta(weeks=1), 0.8)),
            (r'\bnext\s+month\b', lambda m: (reference_date + timedelta(days=30), 0.7)),
        ]
        
        # Apply each pattern
        for pattern, handler in date_patterns:
            for match in re.finditer(pattern, query, re.IGNORECASE):
                try:
                    date_ref = handler(match)
                    if date_ref:
                        date_references.append(date_ref)
                except Exception as e:
                    print(f"Error parsing date reference: {e}")
        
        return date_references
    
    def _parse_date_match(self, match: re.Match, reference_date: datetime) -> Tuple[datetime, float]:
        """Parse a date from a regex match in format MM/DD/YYYY or variations."""
        day, month, year = match.groups()
        
        # Convert to integers
        day = int(day)
        month = int(month)
        year = int(year)
        
        # Handle two-digit years
        if year < 100:
            year = 2000 + year if year < 50 else 1900 + year
        
        # Create datetime object
        try:
            return datetime(year, month, day), 1.0
        except ValueError:
            # If month/day are swapped, try the other way around
            try:
                return datetime(year, day, month), 1.0
            except ValueError:
                return None
    
    def _parse_month_day_match(self, match: re.Match, reference_date: datetime) -> Tuple[datetime, float]:
        """Parse a date from a regex match in format 'Month Day, Year'."""
        month_name, day, year = match.groups()
        
        # Convert month name to number
        month_names = [
            "january", "february", "march", "april", "may", "june", 
            "july", "august", "september", "october", "november", "december"
        ]
        month_abbrevs = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        
        month_name = month_name.lower()
        
        if month_name in month_names:
            month = month_names.index(month_name) + 1
        elif month_name in month_abbrevs:
            month = month_abbrevs.index(month_name) + 1
        else:
            return None
        
        # Convert day to integer
        day = int(day)
        
        # Use current year if not specified
        year = int(year) if year else reference_date.year
        
        # Handle two-digit years
        if year and year < 100:
            year = 2000 + year if year < 50 else 1900 + year
        
        # Create datetime object
        try:
            return datetime(year, month, day), 1.0
        except ValueError:
            return None
    
    def _get_behavior_based_recommendations(self, 
                                          query: str, 
                                          logs: List[Dict[str, Any]],
                                          logs_access_frequency: Dict[str, int]) -> List[Tuple[str, float]]:
        """
        Get recommendations based on user behavior patterns.
        
        Args:
            query: Search query or context
            logs: List of logs
            logs_access_frequency: Dictionary mapping log IDs to access counts
            
        Returns:
            List of (log_id, score) tuples
        """
        # This is a simplified implementation. In a real system, this would incorporate
        # sophisticated user behavior analysis and patterns.
        
        # 1. Use access frequency as a base signal
        behavior_scores = {}
        if logs_access_frequency:
            max_frequency = max(logs_access_frequency.values())
            for log_id, frequency in logs_access_frequency.items():
                # Normalize frequency to 0-1 range
                behavior_scores[log_id] = frequency / max_frequency if max_frequency > 0 else 0
        
        # 2. Find patterns in time-of-day usage
        # Group logs by hour of day
        hour_patterns = {}
        for log in logs:
            log_id = log.get('id')
            if not log_id:
                continue
                
            log_time = datetime.fromisoformat(log.get('start_time', datetime.now().isoformat()))
            hour = log_time.hour
            
            if hour not in hour_patterns:
                hour_patterns[hour] = []
            hour_patterns[hour].append(log_id)
        
        # Boost scores for logs created at similar time of day
        current_hour = datetime.now().hour
        nearby_hours = [(current_hour + i) % 24 for i in range(-1, 2)]  # Current hour +/- 1
        
        for hour in nearby_hours:
            if hour in hour_patterns:
                for log_id in hour_patterns[hour]:
                    # Boost by 0.2 (can be adjusted)
                    if log_id in behavior_scores:
                        behavior_scores[log_id] += 0.2
                    else:
                        behavior_scores[log_id] = 0.2
        
        # Convert to list of tuples, sort by score, and return
        recommendations = [(log_id, min(score, 1.0)) for log_id, score in behavior_scores.items()]
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations
    
    def generate_memory_insights(self, logs: List[Dict[str, Any]], timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Generate insights and patterns from user memory logs.
        
        Args:
            logs: List of user logs
            timeframe_days: Number of days to analyze
            
        Returns:
            Dictionary of insights
        """
        if not logs:
            return {}
        
        # Filter logs to the specified timeframe
        now = datetime.now()
        cutoff_date = now - timedelta(days=timeframe_days)
        
        recent_logs = [
            log for log in logs 
            if datetime.fromisoformat(log.get('start_time', now.isoformat())) >= cutoff_date
        ]
        
        if not recent_logs:
            return {"message": "No logs found in the specified timeframe"}
        
        # Use memory analyzer to identify patterns
        patterns = self.memory_analyzer.identify_patterns(recent_logs)
        
        # Generate temporal connections
        temporal_connections = self.memory_analyzer.generate_temporal_connections(recent_logs)
        
        # Generate semantic connections using memory model if available
        semantic_connections = {}
        try:
            memory_graph = self.memory_model.build_memory_graph(recent_logs, similarity_threshold=0.6)
            semantic_connections = memory_graph
        except Exception as e:
            print(f"Error building memory graph: {e}")
        
        # Extract most frequently mentioned entities
        entity_frequencies = patterns.get('entity_frequency', {})
        top_entities = sorted(entity_frequencies.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Generate time-based insights
        time_patterns = patterns.get('time_of_day', {})
        weekday_patterns = patterns.get('weekday_activity', {})
        
        # Structure the insights
        insights = {
            "timeframe": {
                "start_date": cutoff_date.isoformat(),
                "end_date": now.isoformat(),
                "total_logs": len(recent_logs)
            },
            "activity_patterns": {
                "time_of_day": time_patterns,
                "weekday_activity": weekday_patterns,
            },
            "content_insights": {
                "top_entities": [{"entity": entity, "frequency": freq} for entity, freq in top_entities],
                "semantic_clusters": self._identify_topic_clusters(recent_logs),
            },
            "connection_insights": {
                "temporal_connection_count": sum(len(connections) for connections in temporal_connections.values()),
                "semantic_connection_count": sum(len(connections) for connections in semantic_connections.values()),
                "highly_connected_logs": self._find_highly_connected_logs(temporal_connections, semantic_connections),
            }
        }
        
        return insights
    
    def _identify_topic_clusters(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify topic clusters in logs.
        
        Args:
            logs: List of logs
            
        Returns:
            List of topic cluster information
        """
        # This is a simplified implementation
        # A real implementation would use more sophisticated topic modeling
        
        # Extract all words from logs
        all_words = []
        for log in logs:
            content = log.get('content', '').lower()
            # Simple word tokenization (could be improved)
            words = re.findall(r'\b[a-z]{3,}\b', content)
            all_words.extend(words)
        
        # Remove common stop words
        stop_words = set(['and', 'the', 'to', 'of', 'in', 'for', 'with', 'on', 'at', 'from', 
                          'by', 'about', 'as', 'is', 'was', 'were', 'be', 'been', 'being',
                          'have', 'has', 'had', 'do', 'does', 'did', 'but', 'an', 'this',
                          'that', 'these', 'those', 'am', 'are', 'will', 'would', 'should',
                          'can', 'could', 'may', 'might', 'must', 'shall', 'should'])
        
        filtered_words = [word for word in all_words if word not in stop_words]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        most_common_words = word_counts.most_common(30)
        
        # Group logs by common words (simple clustering)
        clusters = []
        for word, count in most_common_words:
            if count >= 3:  # Only consider words that appear at least 3 times
                cluster_logs = []
                for log in logs:
                    content = log.get('content', '').lower()
                    if re.search(rf'\b{word}\b', content):
                        cluster_logs.append(log.get('id'))
                
                if len(cluster_logs) >= 2:  # Only include clusters with at least 2 logs
                    clusters.append({
                        "topic": word,
                        "log_count": len(cluster_logs),
                        "log_ids": cluster_logs[:10]  # Limit to 10 logs per cluster
                    })
        
        return clusters
    
    def _find_highly_connected_logs(self, 
                                   temporal_connections: Dict[str, List[str]], 
                                   semantic_connections: Dict[str, List[Tuple[str, float]]]) -> List[Dict[str, Any]]:
        """
        Find logs that have many connections to other logs.
        
        Args:
            temporal_connections: Dictionary mapping log IDs to temporal connections
            semantic_connections: Dictionary mapping log IDs to semantic connections
            
        Returns:
            List of highly connected log information
        """
        connection_counts = {}
        
        # Count temporal connections
        for log_id, connections in temporal_connections.items():
            if log_id not in connection_counts:
                connection_counts[log_id] = {"temporal": 0, "semantic": 0, "total": 0}
            connection_counts[log_id]["temporal"] = len(connections)
            connection_counts[log_id]["total"] += len(connections)
        
        # Count semantic connections
        for log_id, connections in semantic_connections.items():
            if log_id not in connection_counts:
                connection_counts[log_id] = {"temporal": 0, "semantic": 0, "total": 0}
            connection_counts[log_id]["semantic"] = len(connections)
            connection_counts[log_id]["total"] += len(connections)
        
        # Sort by total connections and return top logs
        sorted_logs = sorted(connection_counts.items(), key=lambda x: x[1]["total"], reverse=True)
        
        return [{"log_id": log_id, "connections": info} for log_id, info in sorted_logs[:10]]