'use client';

import { useState, useEffect } from "react";
import axios from "axios";

// 使用环境变量设置API基础URL，如果未定义则默认为本地开发URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

export default function Home() {
  const [log, setLog] = useState("");
  const [logs, setLogs] = useState<Array<{id: string, content: string}>>([]);
  const [suggestion, setSuggestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // 在页面加载时获取最近的日志
  useEffect(() => {
    fetchLogs();
  }, []);

  // 从后端获取日志的函数
  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/logs`);
      setLogs(response.data.logs);
    } catch (err) {
      console.error("Error fetching logs:", err);
      setError("Failed to fetch logs. Please check that your backend server is running.");
    } finally {
      setIsLoading(false);
    }
  };

  const addLog = async () => {
    if (!log.trim()) {
      setError("Please enter a log entry");
      return;
    }

    try {
      setIsLoading(true);
      setError("");
      
      await axios.post(`${API_BASE_URL}/api/add-log`, { log });
      
      // 重新获取最新的日志
      await fetchLogs();
      
      // 显示成功消息并3秒后清除
      setSuccessMessage("Log added successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
      
      // 清空输入框
      setLog("");
    } catch (err) {
      console.error("Error adding log:", err);
      setError("Failed to add log. Please check that your backend server is running.");
    } finally {
      setIsLoading(false);
    }
  };

  // 删除日志
  const deleteLog = async (id: string) => {
    try {
      setIsLoading(true);
      await axios.delete(`${API_BASE_URL}/api/logs/${id}`);
      
      // 重新获取日志以更新列表
      await fetchLogs();
      
      setSuccessMessage("Log deleted successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      console.error("Error deleting log:", err);
      setError("Failed to delete log.");
    } finally {
      setIsLoading(false);
    }
  };

  const getSuggestion = async () => {
    try {
      setIsLoading(true);
      setError("");
      
      const response = await axios.get(`${API_BASE_URL}/api/suggestion`);
      setSuggestion(response.data.suggestion);
    } catch (err) {
      console.error("Error getting suggestion:", err);
      setError("Failed to get suggestion. Please check that your backend server is running.");
    } finally {
      setIsLoading(false);
    }
  };

  // 处理表单提交
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addLog();
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6 text-center">Text2Cal</h1>
        
        {/* 日志输入表单 */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Add New Log</h2>
          
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="log" className="block text-sm font-medium text-gray-700 mb-1">
                Log Entry
              </label>
              <textarea
                id="log"
                rows={4}
                className="w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                value={log}
                onChange={(e) => setLog(e.target.value)}
                placeholder="Enter log text here. You can use the format:
@dd/mm/yy 9:00-10:30: Meeting with team
13:00-14:00: Lunch with client"
              />
              <p className="mt-1 text-sm text-gray-500">
                Use format: @dd/mm/yy start_time-end_time: [To-do] for scheduled events.
              </p>
            </div>
            <button
              type="submit"
              className="w-full bg-green-500 text-white p-2 rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
              disabled={isLoading}
            >
              {isLoading ? "Adding..." : "Add Log"}
            </button>
          </form>
          
          {/* 成功/错误信息 */}
          {successMessage && (
            <div className="mt-4 p-2 bg-green-100 text-green-700 rounded-md">
              {successMessage}
            </div>
          )}
          {error && (
            <div className="mt-4 p-2 bg-red-100 text-red-700 rounded-md">
              {error}
            </div>
          )}
        </div>
        
        {/* AI建议 */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Productivity Insights by AI helper</h2>
          <button
            className="mb-4 bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            onClick={getSuggestion}
            disabled={isLoading}
          >
            {isLoading ? "Generating..." : "Generate Productivity Insights"}
          </button>
          {suggestion && (
            <div className="bg-gray-50 p-4 rounded-md whitespace-pre-line">
              {suggestion}
            </div>
          )}
        </div>
        
        {/* 最近的日志 */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Recent Logs</h2>
          {isLoading && <p>Loading logs...</p>}
          {!isLoading && logs.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {logs.map((logItem) => (
                <li key={logItem.id} className="py-3 flex justify-between items-center">
                  <span className="flex-grow">{logItem.content}</span>
                  <div className="flex space-x-2">
                    <button 
                      onClick={() => deleteLog(logItem.id)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            !isLoading && <p className="text-gray-500">No logs found.</p>
          )}
        </div>
      </div>
    </div>
  );
}