'use client';

import { useState, useEffect, useRef } from "react";
import { apiService } from '../services/api';
import memoryAttention from '../services/memoryAttention';
import axios from "axios";
import { Log } from '../types';

// Define your API base URL here
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

// File Upload Component
const FileUploadZone = ({ onUpload }: { onUpload: (file: File) => void }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  
  const handleClick = () => {
    if (inputRef.current) {
      inputRef.current.click();
    }
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files[0]);
      
      // Clear the input value for future uploads
      if (e.target.value) {
        e.target.value = '';
      }
    }
  };
  
  return (
    <div 
      className="drop-zone flex items-center justify-center cursor-pointer"
      onClick={handleClick}
    >
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        className="mr-2 h-4 w-4" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M8 12l4 4 4-4" />
      </svg>
      <span>Upload</span>
      <input 
        type="file" 
        id="fileUpload" 
        ref={inputRef}
        onChange={handleChange}
        accept="image/*,application/pdf,.docx,.doc,.txt"
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default function Home() {
  // Text input states
  const [logText, setLogText] = useState("");
  const [fullMemory, setFullMemory] = useState("");
  
  // Main data states
  const [logs, setLogs] = useState<Log[]>([]);
  const [suggestion, setSuggestion] = useState("");
  const [userAvatar, setUserAvatar] = useState('/api/placeholder/50/50');
  
  // UI states
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isMobile, setIsMobile] = useState(false);
  
  // Synthetic data generation states
  const [isSynthDataModalOpen, setIsSynthDataModalOpen] = useState(false);
  const [synthDataCount, setSynthDataCount] = useState(100);
  
  // Memory visualization states
  const [attentionWeights, setAttentionWeights] = useState<{[key: string]: number}>({});
  const [showAttentionMap, setShowAttentionMap] = useState(true);
  const [selectedMemory, setSelectedMemory] = useState<string | null>(null);
  
  // File analysis states
  const [selectedFileLogId, setSelectedFileLogId] = useState<string | null>(null);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  
  // Memory generation states
  const [isGenerating, setIsGenerating] = useState(false);
  const [originalMemories, setOriginalMemories] = useState<Log[]>([]);
  
  // References
  const logAreaRef = useRef<HTMLDivElement>(null);
  
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
      const logs = await apiService.fetchLogs();
      setLogs(logs);
      
      // Update full memory text when logs change
      updateFullMemoryText(logs);
      
      // Generate attention weights based on recency
      const weights: {[key: string]: number} = {};
      logs.forEach((log, index) => {
        weights[log.id] = Math.max(0.1, 1 - (index * 0.15));
      });
      setAttentionWeights(weights);
      
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Update the full memory text from logs
  const updateFullMemoryText = (logs: Log[]) => {
    const memoryText = logs.map(log => log.content).join('\n\n');
    setFullMemory(memoryText);
  };

  // Add new log
  const handleLogSubmit = async () => {
    if (!logText.trim()) {
      setError("Please enter a log entry");
      return;
    }

    try {
      setIsLoading(true);
      setError("");
      
      await apiService.addLog(logText);
      await fetchLogs();
      
      setSuccessMessage("Memory logged successfully.");
      setLogText("");
      
      // Update full memory text
      setFullMemory(prev => {
        // If starts with @, add double newline
        if (logText.startsWith('@')) {
          return prev + '\n\n' + logText;
        } else {
          // Otherwise just add single space
          return prev + ' ' + logText;
        }
      });
      
      // Get AI suggestion automatically
      await getSuggestion();
      
    } catch (error) {
      console.error("Error:", error);
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
    } catch (error) {
      console.error("Error:", error);
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
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Update in page.tsx, the generateCompletion function
  const generateCompletion = async () => {
    if (logs.length === 0) {
      setError("No memories available to generate completion");
      return;
    }
    
    try {
      setIsGenerating(true);
      setError("");
      
      // Save original memories
      setOriginalMemories(logs);
      
      // Get weighted memories
      const weightedMemories = {};
      for (const log of logs) {
        (weightedMemories as Record<string, number>)[log.id] = attentionWeights[log.id] || 0.5;
      }
      
      // Generate completion
      const result = await apiService.generateMemoryCompletion(
        logs.map(log => log.id),
        weightedMemories
      );
      
      // Store both the full completion and the original content markers
      setFullMemory(result.completion);
      setOriginalContents(result.originalContents);
      
      setSuggestion("Your memory has been enriched with contextual insights based on your attention patterns.");
    } catch (error) {
      console.error("Error generating memory completion:", error);
      setError("Failed to generate memory completion. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  // Add a new state to track original contents
  const [originalContents, setOriginalContents] = useState<string[]>([]);

  // Update the formatMemoryText function to highlight properly
  const formatMemoryText = () => {
    if (!fullMemory) return [];
    
    // Split the text into paragraphs
    const paragraphs = fullMemory.split('\n\n');
    
    return paragraphs.map((paragraph, index) => {
      // Check if this paragraph is one of the original contents
      const isOriginal = originalContents.some(original => 
        paragraph.trim() === original.trim()
      );
      
      return (
        <div 
          key={index} 
          className={isOriginal ? "font-semibold text-black" : "text-gray-700"}
        >
          {paragraph}
        </div>
      );
    });
  };
  
  const [useEnhanced, setUseEnhanced] = useState(true);
  const [openaiRatio, setOpenaiRatio] = useState(0.3);

  // Generate synthetic data
  // Update your function that calls the API
  const generateSyntheticData = async () => {
    if (synthDataCount < 10 || synthDataCount > 1000) {
        setError("Please enter a number between 10 and 1000");
        return;
    }
    
    try {
        setIsLoading(true);
        setError("");
        
        const result = await apiService.generateSyntheticData({
            count: synthDataCount,
            enhanced: useEnhanced,
            openaiRatio: openaiRatio
        });
        setSuccessMessage(`Successfully generated ${result.count} synthetic memory records`);
        setIsSynthDataModalOpen(false);
        
        // Refresh logs
        await fetchLogs();
    } catch (error) {
        console.error("Error generating synthetic data:", error);
        setError("Failed to generate synthetic data. Please try again.");
    } finally {
        setIsLoading(false);
    }
  };

  // Handle file upload
  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    setError("");
    
    try {
      // Create FormData object
      const formData = new FormData();
      formData.append('file', file);
      
      // Send file to backend
      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      // Handle successful response
      if (response.data.status === 'success') {
        setSuccessMessage(`File uploaded successfully: ${file.name}`);
        
        // Save file log ID for later analysis
        if (response.data.log_id) {
          setSelectedFileLogId(response.data.log_id);
          
          // If image file, show analysis option
          if (file.type.startsWith('image/')) {
            setSuccessMessage(`Image uploaded: ${file.name}. You can now analyze this image.`);
          }
        }
        
        // Refresh logs list
        fetchLogs();
      }
    } catch (error) {
      console.error("Error:", error);
      setError("Failed to upload file. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Analyze uploaded file
  const analyzeFile = async () => {
    if (!selectedFileLogId) return;
    
    setIsLoading(true);
    setError("");
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/files/${selectedFileLogId}/analyze`);
      
      if (response.data.status === 'success') {
        setAnalysisResults(response.data);
        setShowAnalysisModal(true);
      }
    } catch (error) {
      console.error("Error:", error);
      setError("Failed to analyze file. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle keyboard events
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleLogSubmit();
    }
  };

  // Memory attention features
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
  
  // Generate new avatar
  const generateAvatar = () => {
    setIsLoading(true);
    
    // Mock avatar generation
    setTimeout(() => {
      // In a real implementation, this would call an image generation API
      const randomSeed = Math.floor(Math.random() * 1000);
      setUserAvatar(`/api/placeholder/50/50?rand=${randomSeed}`);
      setSuggestion("Your avatar has been updated based on your current memory patterns.");
      setIsLoading(false);
    }, 1000);
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

  // Show mobile message on mobile devices
  if (isMobile) {
    return (
      <div className="min-h-screen bg-white flex flex-col justify-center items-center p-4">
        <h1 className="text-2xl font-light mb-6">
          Memory <span className="font-serif italic">Log</span>
        </h1>
        <div className="text-center text-gray-600">
          Mobile version currently not available. Please use a desktop browser for the full experience.
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white p-4 border-b border-gray-200 flex justify-between items-center">
        <h1 className="text-2xl font-light">
          Log your <span className="font-serif italic">Memory</span>...What are you?
        </h1>
        <div 
          className="w-12 h-12 rounded-full bg-blue-500 overflow-hidden cursor-pointer flex items-center justify-center"
          onClick={generateAvatar}
        >
          <img src={userAvatar} alt="Profile" className="w-full h-full object-cover" />
        </div>
      </header>
      
      {/* Main content */}
      <div className="flex-1 flex flex-col md:flex-row">
        {/* Left side - Memory log area */}
        <div className="md:w-2/3 p-6 flex flex-col">
          {/* Input area */}
          <div className="mb-4 flex">
            <input
              type="text"
              value={logText}
              onChange={(e) => setLogText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Log a memory or diary entry (@date for new entries)"
              className="flex-1 p-3 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button 
              onClick={handleLogSubmit}
              className="bg-blue-500 text-white px-4 rounded-r-md hover:bg-blue-600"
              disabled={isLoading}
            >
              {isLoading ? "..." : "Log"}
            </button>
          </div>
          
          {/* Memory text area */}
          <div 
            ref={logAreaRef}
            className="flex-1 bg-white border border-gray-100 rounded-md p-4 mb-4 overflow-auto"
          >
            {isLoading ? (
              <div className="text-center text-gray-500 py-4">Loading memories...</div>
            ) : fullMemory ? (
              <div className="space-y-4">
                {formatMemoryText()}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-4">No memories yet. Start logging your thoughts above.</div>
            )}
          </div>
          
          {/* Controls */}
          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              <button 
                onClick={generateCompletion}
                className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 flex items-center"
                disabled={isGenerating || isLoading}
              >
                {isGenerating ? 'Generating...' : 'Generate Completion'}
              </button>
              
              <FileUploadZone onUpload={handleFileUpload} />
              
              {selectedFileLogId && (
                <button
                  onClick={analyzeFile}
                  className="bg-blue-500 text-white px-3 py-2 rounded-md hover:bg-blue-600"
                  disabled={isLoading}
                >
                  {isLoading ? "Analyzing..." : "Analyze File"}
                </button>
              )}
            </div>
            
            <button
              onClick={() => setShowAttentionMap(!showAttentionMap)}
              className="text-blue-500 hover:text-blue-700"
            >
              {showAttentionMap ? 'Hide Memory Map' : 'Show Memory Map'}
            </button>
          </div>
          
          {/* Notifications */}
          {successMessage && (
            <div className="notification notification-success mt-4">
              {successMessage}
            </div>
          )}
          {error && (
            <div className="notification notification-error mt-4">
              {error}
            </div>
          )}
          
          {/* AI Feedback */}
          {suggestion && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mt-4">
              <h2 className="text-sm font-medium text-blue-700 mb-1">AI Feedback</h2>
              <p className="text-sm text-blue-600">{suggestion}</p>
            </div>
          )}
        </div>
        
        {/* Right side - Memory attention map */}
        {showAttentionMap && (
          <div className="md:w-1/3 bg-white border-l border-gray-200 p-6 overflow-auto">
            <h2 className="text-lg font-medium mb-4">Memory Attention Map</h2>
            <p className="text-sm text-gray-500 mb-4">
              Adjust how different memories influence your experience
            </p>
            
            {logs.length === 0 ? (
              <div className="text-center text-gray-500 py-4">No memories yet to display.</div>
            ) : (
              <div className="grid grid-cols-2 gap-4 mb-6">
                {logs.slice(0, 6).map(memory => (
                  <div 
                    key={memory.id}
                    className={`aspect-circle rounded-md p-2 cursor-pointer flex flex-col justify-between transition-all
                                ${selectedMemory === memory.id ? 'ring-2 ring-blue-500' : ''}`}
                    style={{
                      backgroundColor: `rgba(49, 130, 206, ${attentionWeights[memory.id] || 0.1})`,
                      color: attentionWeights[memory.id] > 0.5 ? 'white' : '#2d3748'
                    }}
                    onClick={() => setSelectedMemory(memory.id === selectedMemory ? null : memory.id)}
                  >
                    <div className="text-xs font-medium flex justify-between">
                      <span>Memory {memory.id.substring(0, 4)}...</span>
                      <span>{Math.round((attentionWeights[memory.id] || 0) * 100)}%</span>
                    </div>
                    <p className="text-xs line-clamp-2 my-1 text-xs">
                      {memory.content.substring(0, 40)}...
                    </p>
                    <div className="flex justify-between text-xs">
                      <button 
                        onClick={(e) => { e.stopPropagation(); deleteLog(memory.id); }}
                        className="hover:underline text-xs"
                      >
                        Delete
                      </button>
                      <span className="text-xs">{formatDate(memory.timestamp || memory.start_time)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* Memory adjustment controls */}
            <div className="flex flex-col gap-2">
              {selectedMemory && (
                <>
                  <button
                    onClick={() => enhanceMemory(selectedMemory)}
                    className="bg-blue-500 text-white px-3 py-2 rounded-md hover:bg-blue-600 text-sm"
                  >
                    Enhance Memory
                  </button>
                  <button
                    onClick={() => reduceMemory(selectedMemory)}
                    className="bg-gray-200 text-gray-800 px-3 py-2 rounded-md hover:bg-gray-300 text-sm"
                  >
                    Reduce Memory
                  </button>
                </>
              )}
              <button
                onClick={resetMemoryWeights}
                className="bg-gray-200 text-gray-800 px-3 py-2 rounded-md hover:bg-gray-300 text-sm"
              >
                Reset Weights
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Recent Memories List */}
      <div className="border-t border-gray-200 bg-white p-6">
        <h2 className="text-lg font-medium mb-4">Recent Memories</h2>
        
        {isLoading ? (
          <div className="text-center text-gray-500 py-4">Loading memories...</div>
        ) : logs.length === 0 ? (
          <div className="text-center text-gray-500 py-4">No memories found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {logs.map((logItem) => (
              <div key={logItem.id} className="border border-gray-200 rounded-md p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs text-gray-500">{formatDate(logItem.timestamp || logItem.start_time)}</span>
                  <button 
                    onClick={() => deleteLog(logItem.id)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
                <p className="text-sm text-gray-700 line-clamp-3">{logItem.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Timeline */}
      <div className="fixed bottom-16 left-0 right-0 mx-auto w-3/4 max-w-4xl px-4">
        <div className="timeline-bar h-1 bg-gray-200 rounded-full overflow-hidden">
          {logs.map((log, index) => {
            const width = 100 / Math.max(logs.length, 1);
            return (
              <div
                key={log.id}
                className="inline-block h-full"
                style={{
                  backgroundColor: `rgba(49, 130, 206, ${attentionWeights[log.id] || 0.5})`,
                  width: `${width}%`,
                }}
              />
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Past</span>
          <span>Present</span>
        </div>
      </div>
      
      {/* Synthetic Data Generator Button */}
      <div className="fixed bottom-24 right-6">
        <button
          onClick={() => setIsSynthDataModalOpen(true)}
          className="bg-purple-500 text-white p-3 rounded-full shadow-lg hover:bg-purple-600 flex items-center justify-center"
          title="Generate synthetic data"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
      
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 px-6 text-center text-xs text-gray-500">
        <p>Memory Log - An experimental tool for personal memory management</p>
        <div className="mt-2 flex justify-center space-x-4">
          <a href="#" className="hover:text-blue-600">About</a>
          <a href="#" className="hover:text-blue-600">Documentation</a>
          <a href="#" className="hover:text-blue-600">GitHub</a>
          <a href="#" className="hover:text-blue-600">Privacy</a>
        </div>
      </footer>
      
      {/* File Analysis Modal */}
      {showAnalysisModal && analysisResults && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-md p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4">File Analysis Results</h2>
            
            {/* Image analysis results */}
            {analysisResults.file_type === 'image' && (
              <div>
                {/* Sensory descriptions */}
                {analysisResults.sensory_descriptions && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium mb-3">Sensory Descriptions</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {Object.entries(analysisResults.sensory_descriptions).map(([sense, data]: [string, any]) => (
                        <div key={sense} className="border border-gray-200 p-3 rounded">
                          <h4 className="font-medium mb-1 capitalize">{sense}</h4>
                          <p className="text-sm text-gray-600">{data.English}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Content analysis */}
                {analysisResults.content_analysis && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium mb-3">Content Analysis</h3>
                    <div className="bg-gray-50 p-4 rounded">
                      <p className="mb-2"><strong>Description:</strong> {analysisResults.content_analysis.description}</p>
                      
                      {analysisResults.content_analysis.objects && (
                        <p className="mb-2"><strong>Objects:</strong> {analysisResults.content_analysis.objects.join(", ")}</p>
                      )}
                      
                      {analysisResults.content_analysis.colors && (
                        <p className="mb-2"><strong>Colors:</strong> {analysisResults.content_analysis.colors.join(", ")}</p>
                      )}
                      
                      {analysisResults.content_analysis.mood && (
                        <p className="mb-2"><strong>Mood:</strong> {analysisResults.content_analysis.mood}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* Document analysis results */}
            {analysisResults.file_type === 'document' && (
              <div>
                <h3 className="text-lg font-medium mb-3">Document Analysis</h3>
                <p className="mb-4"><strong>Summary:</strong> {analysisResults.summary}</p>
                
                {analysisResults.emotion_analysis && (
                  <div className="mb-4">
                    <h4 className="font-medium mb-2">Emotional Tone</h4>
                    <div className="space-y-2">
                      {Object.entries(analysisResults.emotion_analysis).map(([emotion, score]: [string, any]) => (
                        <div key={emotion} className="flex items-center">
                          <div className="w-24 text-sm capitalize">{emotion}</div>
                          <div className="w-full bg-gray-200 rounded-full h-2.5 mx-2">
                            <div 
                              className="bg-blue-600 h-2.5 rounded-full" 
                              style={{width: `${Math.round(score * 100)}%`}}
                            ></div>
                          </div>
                          <div className="w-12 text-xs text-right">{Math.round(score * 100)}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {analysisResults.text_preview && (
                  <div className="bg-gray-50 p-3 rounded text-sm">
                    <h4 className="font-medium mb-2">Text Preview</h4>
                    <p className="whitespace-pre-wrap">{analysisResults.text_preview}</p>
                  </div>
                )}
              </div>
            )}
            
            <div className="flex justify-end mt-6">
              <button 
                onClick={() => setShowAnalysisModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}