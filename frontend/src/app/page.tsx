'use client';

import { useState, useEffect, useCallback } from "react";
import debounce from 'lodash/debounce';
import { apiService } from '../services/api';

export default function Home() {
  const [log, setLog] = useState("");
  const [logs, setLogs] = useState<Array<{id: string, content: string, timestamp?: string, type?: string}>>([]);
  const [suggestion, setSuggestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isMobile, setIsMobile] = useState(false);
  
  // Memory visualization states
  const [attentionWeights, setAttentionWeights] = useState<{[key: string]: number}>({});
  const [showAttentionMap, setShowAttentionMap] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<string | null>(null);

  // Check if device is mobile
  useEffect(() => {
    const checkMobile = () => {
      const isMobileDevice = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent) || window.innerWidth <= 768;
      setIsMobile(isMobileDevice);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);

  // Get recent logs on page load
  useEffect(() => {
    fetchLogs();
  }, []);

  // Fetch logs from API
  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      // const logs = await apiService.getLogs();
      const logs = await apiService.fetchLogs();
      setLogs(logs);
      
      // Generate attention weights based on recency
      const mockWeights: {[key: string]: number} = {};
      logs.forEach((log, index) => {
        mockWeights[log.id] = Math.max(0.1, 1 - (index * 0.15));
      });
      setAttentionWeights(mockWeights);
      
    } catch (err) {
      setError("Failed to fetch logs. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  // Add new log
  const addLog = async () => {
    if (!log.trim()) {
      setError("Please enter a log entry");
      return;
    }

    try {
      setIsLoading(true);
      setError("");
      
      await apiService.addLog(log);
      await fetchLogs();
      
      setSuccessMessage("Memory logged successfully.");
      setLog("");
      
      // Show attention map after adding new log
      setShowAttentionMap(true);
      
      // Generate suggestion automatically
      await getSuggestion();
      
    } catch (err) {
      setError("Failed to add memory log. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  // Delete log
  const deleteLog = async (id: string) => {
    try {
      setIsLoading(true);
      await apiService.deleteLog(id);
      await fetchLogs();
      setSuccessMessage("Memory deleted successfully.");
    } catch (err) {
      setError("Failed to delete memory.");
    } finally {
      setIsLoading(false);
    }
  };

  // Get AI suggestion
  const getSuggestion = async () => {
    try {
      setIsLoading(true);
      setError("");
      const suggestion = await apiService.getSuggestion();
      setSuggestion(suggestion);
    } catch (err) {
      setError("Failed to get insights. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle log button click
  const handleLog = () => {
    addLog();
  };

  // Handle generate button click
  const handleGenerate = () => {
    getSuggestion();
  };

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSuccessMessage("File upload functionality coming soon.");
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  // Handle Enter key in input
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleLog();
    }
  };

  // Memory features
  const enhanceMemory = (id: string) => {
    setSelectedMemory(id);
    const newWeights = {...attentionWeights};
    newWeights[id] = Math.min(1.0, (newWeights[id] || 0.5) + 0.2);
    setAttentionWeights(newWeights);
    setSuccessMessage("Memory influence enhanced.");
    setTimeout(() => setSuccessMessage(""), 2000);
  };
  
  const reduceMemory = (id: string) => {
    setSelectedMemory(id);
    const newWeights = {...attentionWeights};
    newWeights[id] = Math.max(0.1, (newWeights[id] || 0.5) - 0.2);
    setAttentionWeights(newWeights);
    setSuccessMessage("Memory influence reduced.");
    setTimeout(() => setSuccessMessage(""), 2000);
  };
  
  const resetMemoryWeights = () => {
    const newWeights: {[key: string]: number} = {};
    logs.forEach((log, index) => {
      newWeights[log.id] = Math.max(0.1, 1 - (index * 0.15));
    });
    setAttentionWeights(newWeights);
    setSelectedMemory(null);
    setSuccessMessage("Memory weights reset to default.");
    setTimeout(() => setSuccessMessage(""), 2000);
  };

  // Format date for display
  const formatDate = (dateString?: string) => {
    if (!dateString) return "Recent";
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  // Get memory type color
  const getMemoryTypeColor = (type?: string) => {
    switch(type) {
      case 'meeting': return 'rgba(49, 130, 206, 0.8)';
      case 'design': return 'rgba(183, 148, 244, 0.8)';
      case 'research': return 'rgba(79, 209, 197, 0.8)';
      case 'personal': return 'rgba(246, 173, 85, 0.8)';
      default: return 'rgba(49, 130, 206, 0.8)';
    }
  };

  if (isMobile) {
    return (
      <div className="hero-image">
        <div className="mobileMessage">Mobile version currently not available</div>
      </div>
    );
  }

  return (
    <div className="hero-image flex flex-col min-h-screen">
      <div className="w-full max-w-lg px-4 mx-auto flex-grow flex flex-col">
        {/* Main title */}
        <div className="text-center py-8">
          <h1 className="title">
            Log Your <span className="memory-italic">Memory</span>
          </h1>
        </div>

        {/* Input Section */}
        <div className="w-full mb-6">
          <div className="search_box mb-3">
            <input 
              className="query"
              id="query_text"
              value={log}
              onChange={(e) => setLog(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="@03/25/2025 9am-10am Meeting with design team"
              type="text"
            />
          </div>
          
          <div className="buttons">
            <button 
              className="searchBtn"
              onClick={handleLog}
              disabled={isLoading}
            >
              {isLoading ? "Processing..." : "Log"}
            </button>
            
            <label className="drop-zone">
              <input 
                type="file" 
                id="fileUpload" 
                onChange={handleFileUpload}
              />
              Upload
            </label>
            
            <button 
              className="generateBtn"
              onClick={handleGenerate}
              disabled={isLoading} 
            >
              Generate
            </button>
          </div>
        </div>

        {/* Notifications */}
        {successMessage && (
          <div className="notification notification-success mb-4">
            {successMessage}
          </div>
        )}
        {error && (
          <div className="notification notification-error mb-4">
            {error}
          </div>
        )}

        {/* AI Feedback */}
        {suggestion && (
          <div className="ai-feedback mb-6">
            <h2 className="ai-feedback-title">AI Feedback</h2>
            <p>{suggestion}</p>
          </div>
        )}

        {/* Recent Memories */}
        <div className="memory-card mb-8">
          <h2 className="section-title">Recent Memories</h2>
          
          {isLoading ? (
            <div className="p-4 text-sm text-center text-gray-500">Loading memories...</div>
          ) : logs.length === 0 ? (
            <div className="p-4 text-sm text-center text-gray-500">No memories found.</div>
          ) : (
            <ul className="memory-list">
              {logs.map((logItem) => (
                <li key={logItem.id} className="memory-list-item">
                  <span className="memory-list-content">{logItem.content}</span>
                  <div className="flex items-center">
                    <span className="memory-list-date mr-4">{formatDate(logItem.timestamp)}</span>
                    <button 
                      onClick={() => deleteLog(logItem.id)}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Memory Attention Visualization (optional) */}
        {logs.length > 0 && showAttentionMap && (
          <div className="memory-attention-map mb-8">
            <div className="flex justify-between items-center mb-3">
              <h2 className="section-title mb-0">Memory Attention Map</h2>
              <button 
                onClick={() => setShowAttentionMap(!showAttentionMap)}
                className="text-xs text-primary"
              >
                {showAttentionMap ? "Hide" : "Show"}
              </button>
            </div>
            
            <p className="text-xs text-gray-500 mb-3 ml-5">
              Showing how different memories influence current suggestions
            </p>
            
            <div className="space-y-2 mb-4">
              {logs.slice(0, 6).map((logItem) => (
                <div 
                  key={logItem.id} 
                  className={`memory-item ${selectedMemory === logItem.id ? 'selected' : ''}`}
                  style={{
                    backgroundColor: `rgba(49, 130, 206, ${attentionWeights[logItem.id] || 0.1})`,
                    color: attentionWeights[logItem.id] > 0.5 ? 'white' : '#2d3748',
                  }}
                  onClick={() => setSelectedMemory(logItem.id === selectedMemory ? null : logItem.id)}
                >
                  <div className="flex justify-between">
                    <span className="text-xs font-medium">{formatDate(logItem.timestamp)}</span>
                    <span className="text-xs font-medium">{Math.round((attentionWeights[logItem.id] || 0) * 100)}%</span>
                  </div>
                  <p className="text-sm mt-1">{logItem.content}</p>
                </div>
              ))}
            </div>
            
            {/* Memory adjustment controls */}
            <div className="flex space-x-2">
              {selectedMemory && (
                <>
                  <button
                    onClick={() => enhanceMemory(selectedMemory)}
                    className="memory-button memory-button-primary"
                  >
                    Enhance Memory
                  </button>
                  <button
                    onClick={() => reduceMemory(selectedMemory)}
                    className="memory-button memory-button-secondary"
                  >
                    Reduce Memory
                  </button>
                </>
              )}
              <button
                onClick={resetMemoryWeights}
                className="memory-button memory-button-secondary"
              >
                Reset Weights
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="timeline-container">
        <div className="timeline-bar">
          {logs.map((log, index) => {
            const width = 100 / logs.length;
            const position = index * width;
            return (
              <div
                key={log.id}
                className="timeline-segment"
                style={{
                  backgroundColor: getMemoryTypeColor(log.type),
                  width: `${width}%`,
                  left: `${position}%`
                }}
              />
            );
          })}
        </div>
        <div className="timeline-labels">
          <span>Feb</span>
          <span>March</span>
          <span>April</span>
          <span>May</span>
          <span>Present</span>
        </div>
      </div>

      {/* Navigation footer */}
      <section className="navBottom mt-auto">
        <div className="navElement"><a href="https://text2cal.vercel.app/" target="_blank" className="active">Log Your Memory</a></div>
        <div className="navElement"><a href="#" target="_blank">About</a></div>
        <div className="navElement"><a href="#" target="_blank">Documentation</a></div>
        <div className="navElement"><a href="https://github.com/" target="_blank">GitHub</a></div>
        <div className="navElement"><a href="#" target="_blank">Terms</a></div>
        <div className="navElement"><a href="#" target="_blank">Privacy</a></div>
        <div className="navElement"><a href="#" target="_blank">Contact</a></div>
      </section>
    </div>
  );
}