'use client';

import { useState, useEffect, useCallback } from "react";
import debounce from 'lodash/debounce';
import { apiService } from '../services/api';

export default function Home() {
  const [log, setLog] = useState("");
  const [logs, setLogs] = useState<Array<{id: string, content: string, timestamp?: string}>>([]);
  const [suggestion, setSuggestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isMobile, setIsMobile] = useState(false);
  
  // New states for memory visualization
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

  // Optimized fetch logs
  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      const logs = await apiService.getLogs();
      setLogs(logs);
      
      // Generate mock attention weights for demo purposes
      // In a real implementation, this would come from the backend
      const mockWeights: {[key: string]: number} = {};
      logs.forEach((log, index) => {
        // Create decreasing weights based on recency
        mockWeights[log.id] = Math.max(0.1, 1 - (index * 0.15));
      });
      setAttentionWeights(mockWeights);
      
    } catch (err) {
      setError("Failed to fetch logs. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  // Optimized add log
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
      
      setSuccessMessage("Memory logged successfully!");
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

  // Optimized delete log
  const deleteLog = async (id: string) => {
    try {
      setIsLoading(true);
      await apiService.deleteLog(id);
      await fetchLogs();
      setSuccessMessage("Memory deleted successfully!");
    } catch (err) {
      setError("Failed to delete memory.");
    } finally {
      setIsLoading(false);
    }
  };

  // Optimized get suggestion
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

  // Handle search button click
  const handleSearch = () => {
    addLog();
  };

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSuccessMessage("File upload functionality coming soon!");
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  // Handle Enter key in input
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Enhanced memory features
  const enhanceMemory = (id: string) => {
    setSelectedMemory(id);
    // Update weights to emphasize selected memory
    const newWeights = {...attentionWeights};
    // Boost the selected memory's weight
    newWeights[id] = Math.min(1.0, (newWeights[id] || 0.5) + 0.2);
    setAttentionWeights(newWeights);
    setSuccessMessage("Memory influence enhanced!");
    setTimeout(() => setSuccessMessage(""), 2000);
  };
  
  const reduceMemory = (id: string) => {
    setSelectedMemory(id);
    // Update weights to reduce selected memory
    const newWeights = {...attentionWeights};
    // Reduce the selected memory's weight
    newWeights[id] = Math.max(0.1, (newWeights[id] || 0.5) - 0.2);
    setAttentionWeights(newWeights);
    setSuccessMessage("Memory influence reduced!");
    setTimeout(() => setSuccessMessage(""), 2000);
  };
  
  const resetMemoryWeights = () => {
    // Reset to default weights based on recency
    const newWeights: {[key: string]: number} = {};
    logs.forEach((log, index) => {
      newWeights[log.id] = Math.max(0.1, 1 - (index * 0.15));
    });
    setAttentionWeights(newWeights);
    setSelectedMemory(null);
    setSuccessMessage("Memory weights reset to default!");
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

  if (isMobile) {
    return (
      <div className="hero-image">
        <div className="mobileMessage">Mobile version currently not available</div>
      </div>
    );
  }

  return (
    <div className="hero-image flex flex-col min-h-screen">
      <div className="w-full max-w-5xl px-4 mx-auto flex-grow flex flex-col">
        {/* Main title */}
        <div className="text-center py-8">
          <h1 className="title text-3xl md:text-4xl mb-2">
            Log Your <span style={{ fontFamily: 'Times New Roman, serif', fontStyle: 'italic' }}>Memory</span>
          </h1>
        </div>

        {/* Input Section */}
        <div className="w-full max-w-2xl mx-auto mb-8">
          <div className="search_box mb-4">
            <input 
              className="query w-full p-3 text-base rounded-md"
              id="query_text"
              value={log}
              onChange={(e) => setLog(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="@03/25/2025 9am-10am Meeting with design team"
              type="text"
            />
          </div>
          
          <div className="buttons flex gap-4">
            <button 
              className="searchBtn flex-1 py-3 px-4 rounded-md"
              onClick={handleSearch}
              disabled={isLoading}
            >
              {isLoading ? "Processing..." : "search"}
            </button>
            
            <label className="drop-zone flex-1 py-3 px-4 rounded-md text-center">
              <input 
                type="file" 
                id="fileUpload" 
                onChange={handleFileUpload}
              />
              upload
            </label>
          </div>
        </div>

        {/* Success/Error Messages */}
        {successMessage && (
          <div className="w-full max-w-2xl mx-auto mb-4 p-3 bg-green-100 text-green-700 rounded-md">
            {successMessage}
          </div>
        )}
        {error && (
          <div className="w-full max-w-2xl mx-auto mb-4 p-3 bg-red-100 text-red-700 rounded-md">
            {error}
          </div>
        )}

        {/* AI Feedback */}
        {suggestion && (
          <div className="w-full max-w-2xl mx-auto mb-8 p-6 bg-blue-50 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-2">AI Feedback</h2>
            <p className="text-gray-700 whitespace-pre-line">{suggestion}</p>
          </div>
        )}

        {/* Memory Attention Visualization */}
        {logs.length > 0 && showAttentionMap && (
          <div className="w-full max-w-3xl mx-auto mb-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Memory Attention Map</h2>
                <button 
                  onClick={() => setShowAttentionMap(!showAttentionMap)}
                  className="text-blue-500 hover:text-blue-700"
                >
                  {showAttentionMap ? "Hide" : "Show"}
                </button>
              </div>
              
              <p className="text-sm text-gray-500 mb-4">
                Showing how different memories influence current suggestions
              </p>
              
              <div className="space-y-3 mb-6">
                {logs.slice(0, 6).map((logItem) => (
                  <div 
                    key={logItem.id} 
                    className={`p-3 rounded transition-all ${selectedMemory === logItem.id ? 'ring-2 ring-blue-500' : ''}`}
                    style={{
                      backgroundColor: `rgba(66, 153, 225, ${attentionWeights[logItem.id] || 0.1})`,
                      color: attentionWeights[logItem.id] > 0.5 ? 'white' : 'black',
                    }}
                    onClick={() => setSelectedMemory(logItem.id === selectedMemory ? null : logItem.id)}
                  >
                    <div className="flex justify-between">
                      <span className="font-medium">{formatDate(logItem.timestamp)}</span>
                      <span className="font-medium">{Math.round((attentionWeights[logItem.id] || 0) * 100)}%</span>
                    </div>
                    <p>{logItem.content}</p>
                  </div>
                ))}
              </div>
              
              {/* Memory adjustment controls */}
              <div className="flex space-x-3">
                {selectedMemory && (
                  <>
                    <button
                      onClick={() => enhanceMemory(selectedMemory)}
                      className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                    >
                      Enhance Memory
                    </button>
                    <button
                      onClick={() => reduceMemory(selectedMemory)}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Reduce Memory
                    </button>
                  </>
                )}
                <button
                  onClick={resetMemoryWeights}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Reset Weights
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Recent Logs */}
        <div className="w-full max-w-2xl mx-auto mb-16">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Recent Memories</h2>
            {isLoading && <p>Loading memories...</p>}
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
              !isLoading && <p className="text-gray-500">No memories found.</p>
            )}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="fixed left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[70%] max-w-3xl" 
          style={{ top: '70vh' }}>  {/* 将位置改为屏幕高度的70% */}
        <div className="h-6 w-full bg-gray-200 rounded-full overflow-hidden"> {/* 增加高度从h-2到h-4 */}
          <div 
            className="h-full bg-blue-500 transition-all duration-500 ease-out"
            style={{ width: `${Math.min(100, (logs.length / 10) * 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Feb</span>
          <span>March</span>
          <span>April</span>
          <span>May</span>
          <span>Present</span>
        </div>
      </div>

      {/* Navigation section at bottom */}
      <section className="navBottom mt-auto py-4">
        <div className="navElement"><a href="https://text2cal.vercel.app/" target="_blank">Log Your Memory</a></div>
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