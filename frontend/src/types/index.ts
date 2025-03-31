export interface Log {
  id: string;
  content: string;
  start_time?: string;
  end_time?: string;
  category?: string;
  tags?: string[];
  importance?: number;
  timestamp?: string;
}

export interface MemoryAnalysis {
  sensory_descriptions?: any;
  content_analysis?: any;
  summary?: string;
  emotion_analysis?: {[key: string]: number};
  text_preview?: string;
}