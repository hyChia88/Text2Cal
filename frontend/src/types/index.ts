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

// export interface MemoryAnalysis {
//   // Replace 'any' with more specific types
//   sensory_descriptions?: {
//     sight?: { English?: string; Mandarin?: string };
//     sound?: { English?: string; Mandarin?: string };
//     smell?: { English?: string; Mandarin?: string };
//     touch?: { English?: string; Mandarin?: string };
//     taste?: { English?: string; Mandarin?: string };
//     emotion?: { English?: string; Mandarin?: string };
//     [key: string]: { English?: string; Mandarin?: string } | undefined;
//   };
  
//   content_analysis?: {
//     description?: string;
//     objects?: string[];
//     colors?: string[];
//     spatial_relationships?: string;
//     text_content?: string;
//     mood?: string;
//     context?: string;
//     [key: string]: string | string[] | undefined;
//   };
  
//   summary?: string;
//   emotion_analysis?: {[key: string]: number};
//   text_preview?: string;
// }

export interface MemoryAnalysis {
  sensory_descriptions?: {
    [key: string]: { English?: string; Mandarin?: string } | undefined;
  };
  
  content_analysis?: {
    description?: string;
    [key: string]: string | string[] | undefined;
  };
  
  summary?: string;
  emotion_analysis?: {[key: string]: number};
  text_preview?: string;
}