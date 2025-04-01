import axios from 'axios';

// Define the base URL for API requests
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';

// Define types for our API responses
interface Log {
  id: string;
  content: string;
  start_time: string;
  end_time?: string;
  category?: string;
  tags?: string[];
  importance?: number;
  formatted?: string;
}

// This interface is unused - either remove it or use it 
// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface ApiResponse<T> {
  status: string;
  data?: T;
  message?: string;
}

// Define response interfaces for specific endpoints
interface LogConnection {
  id: string;
  content: string;
  start_time: string;
  connection_type: string;
  explanation: string;
  similarity_score: number;
}

interface UploadResponse {
  status: string;
  file_path?: string;
  metadata?: Record<string, unknown>;
  summary?: string;
  log_id?: string;
}

interface AnalysisResponse {
  status: string;
  file_type?: string;
  sensory_descriptions?: Record<string, unknown>;
  content_analysis?: Record<string, unknown>;
  summary?: string;
  emotion_analysis?: Record<string, number>;
  text_preview?: string;
}

interface StatsResponse {
  total_logs: number;
  logs_by_category: Record<string, number>;
  logs_by_day: Record<string, number>;
  logs_by_hour: Record<string, number>;
  most_active_days: Array<[string, number]>;
  most_active_hours: Array<[string, number]>;
  [key: string]: unknown; // Allow additional properties
}

// Create the API service object
export const apiService = {
  // Fetch all logs
  fetchLogs: async (days: number = 30, category?: string, tag?: string, query?: string): Promise<Log[]> => {
    try {
      let url = `${API_BASE_URL}/api/logs?days=${days}`;
      
      if (category) url += `&category=${encodeURIComponent(category)}`;
      if (tag) url += `&tag=${encodeURIComponent(tag)}`;
      if (query) url += `&query=${encodeURIComponent(query)}`;
      
      const response = await axios.get(url);
      return response.data.logs || [];
    } catch (error) {
      console.error('Error fetching logs:', error);
      throw error;
    }
  },
  
  // Add a new log
  addLog: async (content: string): Promise<string> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/add-log`, { log: content });
      return response.data.log_id || response.data.log_ids?.[0] || '';
    } catch (error) {
      console.error('Error adding log:', error);
      throw error;
    }
  },
  
  // Delete a log
  deleteLog: async (logId: string): Promise<boolean> => {
    try {
      const response = await axios.delete(`${API_BASE_URL}/api/logs/${logId}`);
      return response.data.status === 'success';
    } catch (error) {
      console.error('Error deleting log:', error);
      throw error;
    }
  },
  
  // Get a specific log
  getLog: async (logId: string): Promise<Log> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/logs/${logId}`);
      return response.data.log;
    } catch (error) {
      console.error('Error getting log:', error);
      throw error;
    }
  },
  
  // Update a log
  updateLog: async (logId: string, updates: Partial<Log>): Promise<boolean> => {
    try {
      const response = await axios.put(`${API_BASE_URL}/api/logs/${logId}`, updates);
      return response.data.status === 'success';
    } catch (error) {
      console.error('Error updating log:', error);
      throw error;
    }
  },
  
  // Get AI suggestion
  getSuggestion: async (language: string = 'en'): Promise<string> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/suggestion?language=${language}`);
      return response.data.suggestion || '';
    } catch (error) {
      console.error('Error getting suggestion:', error);
      throw error;
    }
  },
  
  // Search logs
  searchLogs: async (query: string, maxResults: number = 10): Promise<Log[]> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/search`, { 
        query, 
        max_results: maxResults 
      });
      return response.data.results || [];
    } catch (error) {
      console.error('Error searching logs:', error);
      throw error;
    }
  },
  
  // Get connections for a log
  getLogConnections: async (logId: string): Promise<LogConnection[]> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/connections/${logId}`);
      return response.data.connections || [];
    } catch (error) {
      console.error('Error getting log connections:', error);
      throw error;
    }
  },
  
  // Upload a file
  uploadFile: async (file: File): Promise<UploadResponse> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  },
  
  // Analyze a file
  analyzeFile: async (logId: string): Promise<AnalysisResponse> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/files/${logId}/analyze`);
      return response.data;
    } catch (error) {
      console.error('Error analyzing file:', error);
      throw error;
    }
  },
  
  // Get statistics 
  getStats: async (days: number = 30): Promise<StatsResponse> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/stats?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error getting stats:', error);
      throw error;
    }
  },
  
  // Generate synthetic data
  generateSyntheticData: async (
    count: number, 
    useEnhanced: boolean = true,
    openaiRatio: number = 0.3
  ): Promise<{count: number}> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate-synthetic-data`, { 
        num_samples: count,
        use_enhanced: useEnhanced,
        openai_ratio: openaiRatio
      });
      return { count: response.data.count || 0 };
    } catch (error) {
      console.error("Error generating synthetic data:", error);
      throw error;
    }
  },
  
  // Generate memory completion
  generateMemoryCompletion: async (memoryIds: string[], weights: {[key: string]: number}): Promise<{
    completion: string, 
    originalContents: string[]
  }> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate-memory-completion`, {
        memory_ids: memoryIds,
        weights: weights
      });
      
      return {
        completion: response.data.completion || "",
        originalContents: response.data.original_contents || []
      };
    } catch (error) {
      console.error("Error generating memory completion:", error);
      throw error;
    }
  }
};