import axios from 'axios';
import { Log } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

/**
 * MemoryAttention service handles memory completion and attention mechanisms
 */
const memoryAttention = {
  /**
   * Generate a memory completion based on existing logs and their attention weights
   * 
   * @param logs - Array of log entries
   * @param weights - Object mapping log IDs to their attention weights
   * @returns Completed memory text
   */
  generateCompletion: async (logs: Log[], weights: {[key: string]: number}): Promise<string> => {
    try {
      // Get memory IDs
      const memoryIds = logs.map(log => log.id);
      
      // Use the API service directly
      const response = await axios.post(`${API_BASE_URL}/api/generate-memory`, {
        memoryIds,
        weights
      });
      return response.data.completion;
    } catch (error) {
      console.error("Error generating memory completion:", error);
      // Fallback to mock generation only if API fails
      return mockGenerateCompletion(logs.map(log => log.content).join('\n\n'));
    }
  },
  
  /**
   * Analyze the emotional tone of memory content
   * 
   * @param content - Memory content to analyze
   * @returns Emotion analysis object
   */
  analyzeEmotionalTone: async (content: string): Promise<{[key: string]: number}> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze-emotion`, {
        content
      });
      
      if (response.data && response.data.emotions) {
        return response.data.emotions;
      }
      
      // Fallback
      return {
        joy: 0.4,
        sadness: 0.1,
        anger: 0.05,
        fear: 0.05,
        surprise: 0.2,
        neutral: 0.2
      };
    } catch (error) {
      console.error("Error analyzing emotional tone:", error);
      // Default fallback
      return {
        joy: 0.4,
        sadness: 0.1,
        anger: 0.05,
        fear: 0.05,
        surprise: 0.2,
        neutral: 0.2
      };
    }
  }
};

/**
 * Mock function to generate a memory completion when API is unavailable
 * 
 * @param originalText - Original memory text
 * @returns Completed memory text
 */
function mockGenerateCompletion(originalText: string): string {
  // Append a mock completion to the original text
  return originalText + "\n\n" + 
    "I've been noticing patterns in my work habits lately. " +
    "When I take short breaks and go for walks, my productivity seems to improve significantly. " +
    "Maybe I should schedule regular outdoor time between tasks. " +
    "The meeting with Sarah yesterday gave me some clarity about next steps. " +
    "I should focus on building the prototype before our next design review.";
}

export default memoryAttention;