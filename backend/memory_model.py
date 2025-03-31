import numpy as np
import os
import json
from typing import List, Dict, Any, Tuple, Optional, Callable
from datetime import datetime
import requests

class MemoryModel:
    """
    Provides embedding and retrieval functionality for memory processing.
    This class handles the deep learning aspects of the memory system, including
    generating embeddings, training custom models, and providing interfaces for
    semantic search and memory retrieval.
    """
    
    def __init__(self, 
                 embedding_api_key: Optional[str] = None,
                 embedding_dimension: int = 1536,
                 model_path: Optional[str] = None):
        """
        Initialize the MemoryModel.
        
        Args:
            embedding_api_key: API key for external embedding service (e.g., OpenAI)
            embedding_dimension: Dimension of embedding vectors
            model_path: Path to saved model weights (if using local model)
        """
        self.embedding_api_key = embedding_api_key
        self.embedding_dimension = embedding_dimension
        self.model_path = model_path
        self.embeddings_cache = {}  # Cache for text embeddings
        
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            A numpy array containing the embedding vector
        """
        # Check cache first to avoid redundant API calls
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        # Use OpenAI's embedding API if key is provided
        if self.embedding_api_key:
            try:
                embedding = self._get_openai_embedding(text)
                self.embeddings_cache[text] = embedding
                return embedding
            except Exception as e:
                print(f"Error getting OpenAI embedding: {e}")
                # Fall back to simple embedding if API fails
        
        # Fallback to a simple embedding method
        embedding = self._get_simple_embedding(text)
        self.embeddings_cache[text] = embedding
        return embedding
    
    def _get_openai_embedding(self, text: str) -> np.ndarray:
        """
        Get embeddings from OpenAI's API.
        
        Args:
            text: The text to embed
            
        Returns:
            A numpy array with the embedding
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.embedding_api_key}"
        }
        
        payload = {
            "input": text,
            "model": "text-embedding-ada-002"  # Use the appropriate OpenAI embedding model
        }
        
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} {response.text}")
        
        embedding_data = response.json()
        embedding = np.array(embedding_data["data"][0]["embedding"])
        return embedding
    
    def _get_simple_embedding(self, text: str) -> np.ndarray:
        """
        Create a simple embedding using TF-IDF-like approach.
        This is a fallback when no external embedding service is available.
        
        Args:
            text: The text to embed
            
        Returns:
            A numpy array with the simple embedding
        """
        # Simple vocabulary of common words (can be expanded)
        vocab = set([
            "meeting", "task", "project", "deadline", "call", "email", "report",
            "presentation", "work", "home", "family", "friend", "lunch", "dinner",
            "morning", "afternoon", "evening", "night", "today", "tomorrow", 
            "yesterday", "week", "month", "year", "important", "urgent", "reminder"
        ])
        
        # Create a simple bag-of-words representation
        words = text.lower().split()
        word_counts = {word: words.count(word) for word in set(words) if word in vocab}
        
        # Create a sparse vector
        vector = np.zeros(len(vocab))
        for i, word in enumerate(vocab):
            if word in word_counts:
                vector[i] = word_counts[word]
        
        # Normalize the vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        # Pad or truncate to match embedding dimension
        if len(vector) < self.embedding_dimension:
            padded = np.zeros(self.embedding_dimension)
            padded[:len(vector)] = vector
            return padded
        else:
            return vector[:self.embedding_dimension]
    
    def compute_similarity(self, embed1: np.ndarray, embed2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embedding vectors.
        
        Args:
            embed1: First embedding vector
            embed2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        # Ensure embeddings have the same dimension
        if embed1.shape != embed2.shape:
            raise ValueError(f"Embedding dimensions don't match: {embed1.shape} vs {embed2.shape}")
            
        # Compute cosine similarity: dot product of normalized vectors
        similarity = np.dot(embed1, embed2) / (np.linalg.norm(embed1) * np.linalg.norm(embed2))
        
        # Handle potential numerical issues
        if np.isnan(similarity):
            return 0.0
        
        return float(similarity)
    
    def find_similar_logs(self, query_embedding: np.ndarray, 
                          log_embeddings: Dict[str, np.ndarray],
                          top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find the most similar logs to a query based on embedding similarity.
        
        Args:
            query_embedding: Embedding of the query
            log_embeddings: Dictionary mapping log IDs to their embeddings
            top_k: Number of results to return
            
        Returns:
            List of (log_id, similarity_score) tuples for the top matches
        """
        similarities = []
        
        for log_id, embedding in log_embeddings.items():
            similarity = self.compute_similarity(query_embedding, embedding)
            similarities.append((log_id, similarity))
        
        # Sort by similarity (descending) and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def build_memory_graph(self, 
                           logs: List[Dict[str, Any]], 
                           similarity_threshold: float = 0.7) -> Dict[str, List[Tuple[str, float]]]:
        """
        Build a graph of memory connections based on semantic similarity.
        
        Args:
            logs: List of log dictionaries
            similarity_threshold: Minimum similarity score to consider logs connected
            
        Returns:
            Dictionary mapping log IDs to lists of (connected_log_id, similarity) tuples
        """
        # Create embeddings for all logs
        log_embeddings = {}
        for log in logs:
            log_id = log.get('id')
            content = log.get('content', '')
            log_embeddings[log_id] = self.get_embedding(content)
        
        # Build the graph
        memory_graph = {}
        log_ids = list(log_embeddings.keys())
        
        for i, log_id in enumerate(log_ids):
            memory_graph[log_id] = []
            
            # Compare with all other logs
            for j, other_log_id in enumerate(log_ids):
                if i != j:  # Skip self-comparison
                    similarity = self.compute_similarity(
                        log_embeddings[log_id], 
                        log_embeddings[other_log_id]
                    )
                    
                    if similarity >= similarity_threshold:
                        memory_graph[log_id].append((other_log_id, similarity))
            
            # Sort connections by similarity (descending)
            memory_graph[log_id].sort(key=lambda x: x[1], reverse=True)
            
        return memory_graph
    
    def save_embeddings(self, embeddings: Dict[str, np.ndarray], filepath: str) -> None:
        """
        Save embeddings to a file.
        
        Args:
            embeddings: Dictionary mapping IDs to embedding vectors
            filepath: Path to save the embeddings
        """
        # Convert numpy arrays to lists for JSON serialization
        serializable_embeddings = {
            id: embedding.tolist() for id, embedding in embeddings.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(serializable_embeddings, f)
    
    def load_embeddings(self, filepath: str) -> Dict[str, np.ndarray]:
        """
        Load embeddings from a file.
        
        Args:
            filepath: Path to the embeddings file
            
        Returns:
            Dictionary mapping IDs to embedding vectors
        """
        if not os.path.exists(filepath):
            return {}
        
        with open(filepath, 'r') as f:
            serialized_embeddings = json.load(f)
        
        # Convert lists back to numpy arrays
        embeddings = {
            id: np.array(embedding) for id, embedding in serialized_embeddings.items()
        }
        
        return embeddings
    
    def get_attention_weights(self, 
                              query: str,
                              logs: List[Dict[str, Any]],
                              temporal_factor: float = 0.3) -> Dict[str, float]:
        """
        Calculate attention weights for logs based on query relevance and temporal information.
        
        Args:
            query: The query or context string
            logs: List of logs to analyze
            temporal_factor: Weight given to temporal recency vs semantic similarity
            
        Returns:
            Dictionary mapping log IDs to their attention weights
        """
        query_embedding = self.get_embedding(query)
        attention_weights = {}
        now = datetime.now()
        
        # Get embeddings for all logs
        log_embeddings = {}
        for log in logs:
            log_id = log.get('id')
            content = log.get('content', '')
            log_embeddings[log_id] = self.get_embedding(content)
        
        # Compute semantic similarity component
        for log in logs:
            log_id = log.get('id')
            
            # Semantic similarity (0-1)
            similarity = self.compute_similarity(query_embedding, log_embeddings[log_id])
            
            # Temporal recency (0-1)
            log_date = datetime.fromisoformat(log.get('start_time', now.isoformat()))
            days_ago = (now - log_date).days
            recency = np.exp(-days_ago / 30)  # Exponential decay with 30-day half-life
            
            # Combine semantic and temporal components
            attention = (1 - temporal_factor) * similarity + temporal_factor * recency
            attention_weights[log_id] = float(attention)
        
        # Normalize to sum to 1
        total_weight = sum(attention_weights.values())
        if total_weight > 0:
            for log_id in attention_weights:
                attention_weights[log_id] /= total_weight
        
        return attention_weights
    
    def clear_embedding_cache(self) -> None:
        """Clear the embedding cache to free memory."""
        self.embeddings_cache = {}
    
    # !! new: 在memory_model.py中添加

    def get_lightweight_attention(self, 
                                query_embedding: np.ndarray, 
                                memory_embeddings: Dict[str, np.ndarray],
                                timestamps: Dict[str, str] = None,
                                user_weights: Dict[str, float] = None) -> Dict[str, float]:
        """
        Calculate lightweight attention weights
        
        Args:
            query_embedding: Query embedding vector
            memory_embeddings: Mapping of memory IDs to embedding vectors
            timestamps: Mapping of memory IDs to timestamps
            user_weights: User-defined weights (memory ID to weight mapping)
            
        Returns:
            Mapping of memory IDs to attention scores
        """
        if not memory_embeddings:
            return {}
        
        # Calculate cosine similarity
        similarity_scores = {}
        for memory_id, embedding in memory_embeddings.items():
            similarity = self.compute_similarity(query_embedding, embedding)
            similarity_scores[memory_id] = max(0, similarity)  # Ensure non-negative
        
        # Apply time decay
        if timestamps:
            now = datetime.now()
            for memory_id, timestamp in timestamps.items():
                if memory_id in similarity_scores:
                    try:
                        time_delta = (now - datetime.fromisoformat(timestamp)).days
                        decay_factor = np.exp(-time_delta / 30)  # 30-day half-life
                        similarity_scores[memory_id] *= decay_factor
                    except (ValueError, TypeError):
                        # Skip decay if timestamp format is invalid
                        pass
        
        # Blend with user weights
        if user_weights:
            for memory_id, weight in user_weights.items():
                if memory_id in similarity_scores:
                    # 70% similarity, 30% user weight
                    similarity_scores[memory_id] = 0.7 * similarity_scores[memory_id] + 0.3 * weight
        
        # Normalize scores
        total = sum(similarity_scores.values())
        if total > 0:
            for memory_id in similarity_scores:
                similarity_scores[memory_id] /= total
        
        return similarity_scores