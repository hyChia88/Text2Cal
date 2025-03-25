import axios from 'axios';
import { Log } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

export const apiService = {
  async fetchLogs(): Promise<Log[]> {
    const response = await axios.get(`${API_BASE_URL}/api/logs`);
    return response.data.logs;
  },

  async addLog(log: string): Promise<void> {
    await axios.post(`${API_BASE_URL}/api/add-log`, { log });
  },

  async deleteLog(id: string): Promise<void> {
    await axios.delete(`${API_BASE_URL}/api/logs/${id}`);
  },

  async getSuggestion(): Promise<string> {
    const response = await axios.get(`${API_BASE_URL}/api/suggestion`);
    return response.data.suggestion;
  }
};