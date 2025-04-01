import os
from typing import List, Dict, Any, Optional, Union
import json
import re
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIHelper:
    """
    Provides OpenAI API integration for memory analysis and suggestion generation.
    Extends the basic OpenAI functionality with memory-specific features.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI helper.
        
        Args:
            api_key: OpenAI API key, if None tries to get from environment variable
        """
        print("Attempting to retrieve OpenAI API key...")
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            print("CRITICAL ERROR: No OpenAI API key found!")
            print("Environment variables:", os.environ)
        else:
            print("OpenAI API key retrieved successfully")
        # Base API URL
        self.api_base_url = "https://api.openai.com/v1"
        
        # Default parameters for API requests
        self.default_params = {
            "model": "gpt-3.5-turbo",  # Can be overridden in specific methods
            "temperature": 0.7,
            "max_tokens": 500,
        }
    
    def _call_openai_api(self, 
                         endpoint: str, 
                         payload: Dict[str, Any], 
                         params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a call to the OpenAI API.
        
        Args:
            endpoint: API endpoint to call
            payload: Request payload
            params: Additional parameters to include in the request
            
        Returns:
            Response from the API
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Merge default parameters with provided ones
        if params:
            for key, value in params.items():
                payload[key] = value
        
        # Make the API request
        response = requests.post(
            f"{self.api_base_url}/{endpoint}",
            headers=headers,
            json=payload
        )
        
        # Check for errors
        if response.status_code != 200:
            error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
            print(error_msg)
            raise Exception(error_msg)
        
        return response.json()
    
    def generate_log_summary(self, logs: List[Dict[str, Any]], 
                           max_length: int = 200) -> str:
        """
        Generate a concise summary of a collection of logs.
        
        Args:
            logs: List of log dictionaries
            max_length: Maximum length of the summary
            
        Returns:
            Summary text
        """
        if not logs:
            return "No logs to summarize."
        
        # Extract log contents
        log_contents = []
        for log in logs:
            timestamp = ""
            if 'start_time' in log:
                try:
                    dt = datetime.fromisoformat(log['start_time'])
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            content = log.get('content', '')
            log_contents.append(f"{timestamp}: {content}")
        
        # Limit the total content length to avoid exceeding API limits
        combined_content = "\n".join(log_contents)
        if len(combined_content) > 4000:
            combined_content = combined_content[:4000] + "..."
        
        # Prepare the prompt
        prompt = f"""Below are several log entries. Please provide a concise summary (maximum {max_length} characters) 
        that captures the key activities, patterns, and important information:

        {combined_content}
        """
        
        # Call the OpenAI API
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant that summarizes log entries concisely."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_openai_api(
                "chat/completions",
                {
                    "messages": messages,
                    "model": "gpt-3.5-turbo",
                    "max_tokens": min(max_length // 2, 500),  # Adjust token limit based on desired length
                    "temperature": 0.5,  # Lower temperature for more focused summary
                }
            )
            
            # Extract and return the summary
            summary = response['choices'][0]['message']['content'].strip()
            return summary
            
        except Exception as e:
            print(f"Error generating log summary: {e}")
            return "Unable to generate summary due to an error."
    
    def generate_suggestion(self, recent_logs: List[Dict[str, Any]], language: str = "en") -> str:
        """
        Generate productivity suggestions based on recent logs.
        
        Args:
            recent_logs: List of recent log entries
            language: Language code ("en" for English, "zh" for Chinese)
            
        Returns:
            Generated suggestion text
        """
        if not recent_logs:
            if language == "zh":
                return "没有找到最近的日志记录，无法生成建议。请添加一些日志，然后再试一次。"
            else:
                return "No recent logs found. Please add some logs and try again."
        
        # Extract log content and dates
        formatted_logs = []
        for log in recent_logs:
            log_date = "No date"
            if 'start_time' in log:
                try:
                    dt = datetime.fromisoformat(log['start_time'])
                    log_date = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            content = log.get('content', '')
            formatted_logs.append(f"[{log_date}] {content}")
        
        logs_text = "\n".join(formatted_logs)
        
        # Prepare system message and prompt based on language
        if language == "zh":
            system_message = "你是一位专业的效率顾问，专注于帮助用户分析他们的日常活动并提供改进建议。"
            prompt = f"""以下是用户最近的日志记录：

{logs_text}

作为用户的时间管理助手，请帮助分析及审视这些日程安排，并提供以下方面的建议（如有）：

1. 时间管理模式
2. 效率提升机会
3. 重复任务自动化的可能性
4. 其他可能的改进建议

请提供具体、可操作的建议，帮助用户提高工作效率。回答应简洁明了，不超过3-4个段落。"""
        else:
            system_message = "You are a professional efficiency consultant focused on helping users analyze their daily activities and provide improvement suggestions."
            prompt = f"""Here are the user's recent log entries:

{logs_text}

As the user's time management assistant, please analyze these logs and provide suggestions on the following aspects (if applicable):

1. Time management patterns
2. Efficiency improvement opportunities
3. Potential for automating repetitive tasks
4. Other possible improvement suggestions

Please provide specific, actionable suggestions to help the user improve productivity. Keep your answer concise, within 1-2 paragraphs, avoid unnesccessary details."""
        
        # Call the OpenAI API
        try:
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_openai_api(
                "chat/completions",
                {
                    "messages": messages,
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 500,
                    "temperature": 0.7,
                }
            )
            
            # Extract and return the suggestion
            suggestion = response['choices'][0]['message']['content'].strip()
            return suggestion
            
        except Exception as e:
            print(f"Error generating suggestion: {e}")
            if language == "zh":
                return f"生成建议时遇到错误：{str(e)}"
            else:
                return f"Error generating suggestion: {str(e)}"
    
    def analyze_log_emotion(self, log_content: str) -> Dict[str, float]:
        """
        Analyze the emotional tone of a log entry.
        
        Args:
            log_content: Content of the log
            
        Returns:
            Dictionary with emotion scores
        """
        if not log_content:
            return {"neutral": 1.0}
        
        prompt = f"""Analyze the emotional tone of the following text. 
        Rate the presence of the following emotions on a scale from 0 to 1, 
        where 0 means "not present" and 1 means "strongly present": 
        joy, sadness, anger, fear, surprise, neutral.

        Text: "{log_content}"
        
        Provide your response as a JSON object with the emotion names as keys and scores as values.
        """
        
        try:
            messages = [
                {"role": "system", "content": "You are an emotion analysis assistant that provides objective emotional tone analysis."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_openai_api(
                "chat/completions",
                {
                    "messages": messages,
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 150,
                    "temperature": 0.2,  # Lower temperature for more consistent rating
                }
            )
            
            # Extract and parse the JSON response
            response_text = response['choices'][0]['message']['content'].strip()
            
            # Sometimes the model might add text before or after the JSON
            # Find the JSON portion using regex
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                emotion_scores = json.loads(json_str)
                
                # Normalize scores if needed
                total = sum(emotion_scores.values())
                if total > 0:
                    normalized_scores = {k: v/total for k, v in emotion_scores.items()}
                    return normalized_scores
                
                return emotion_scores
            else:
                # Fallback if parsing fails
                return {"neutral": 1.0}
            
        except Exception as e:
            print(f"Error analyzing log emotion: {e}")
            return {"neutral": 1.0, "error": str(e)}
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI's embeddings API.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            response = self._call_openai_api(
                "embeddings",
                {
                    "input": texts,
                    "model": "text-embedding-ada-002"
                }
            )
            
            # Extract embeddings from response
            embeddings = [item['embedding'] for item in response['data']]
            return embeddings
            
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []
    
    def get_sensory_descriptions(self, image_path: str, language: str = "en") -> Dict[str, Dict[str, str]]:
        """
        Generate sensory descriptions for an image based on ref2_generate_sensory_descriptions.ipynb.
        
        Args:
            image_path: Path to the image
            language: Language code ("en" for English, "zh" for Chinese)
            
        Returns:
            Dictionary of sensory descriptions
        """
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Prepare the prompt based on language
        if language == "zh":
            prompt = f"""
为图像生成感官描述，包括以下类别的中文描述：
- sight（视觉）: 描述图像的视觉元素，包括颜色、形状、光线等
- sound（听觉）: 描述图像可能的声音
- smell（嗅觉）: 描述图像可能的气味
- touch（触觉）: 描述图像中物体的触感
- taste（味觉）: 描述图像可能联想到的味道
- emotion（情感）: 描述图像可能引发的情感反应

请使用JSON格式输出，每个感官类别包含一个"Chinese"键。
"""
        else:
            prompt = f"""
Generate sensory descriptions for an image, including descriptions for the following categories:
- sight: Describe the visual elements in the image, including colors, shapes, lighting, etc.
- sound: Describe the potential sounds associated with the image
- smell: Describe the potential smells associated with the image
- touch: Describe the tactile sensations associated with objects in the image
- taste: Describe the potential tastes that might be associated with the image
- emotion: Describe the emotional response the image might evoke

Please provide the output in JSON format with each sensory category containing an "English" key.
"""
        
        # Call the OpenAI API using vision model
        try:
            # Read the image file
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                
            # Encode the image as base64
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare the messages with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # Make API call to GPT-4 Vision
            response = self._call_openai_api(
                "chat/completions",
                {
                    "messages": messages,
                    "model": "gpt-4-vision-preview",  # Use vision-capable model
                    "max_tokens": 800,
                }
            )
            
            # Extract and parse the JSON response
            response_text = response['choices'][0]['message']['content'].strip()
            
            # Find the JSON portion using regex
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                descriptions = json.loads(json_str)
                return descriptions
            else:
                # If regex fails, try to parse the whole response as JSON
                try:
                    descriptions = json.loads(response_text)
                    return descriptions
                except:
                    raise ValueError("Failed to parse JSON response")
            
        except Exception as e:
            print(f"Error generating sensory descriptions: {e}")
            # Return empty descriptions on error
            return {
                "sight": {language: ""},
                "sound": {language: ""},
                "smell": {language: ""},
                "touch": {language: ""},
                "taste": {language: ""},
                "emotion": {language: ""}
            }
    
    def analyze_image_content(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze the content of an image using OpenAI's vision capabilities.
        Integrates functionality similar to ref3 and ref4 notebooks.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Dictionary with image analysis results
        """
        # Check if file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Prepare prompt for comprehensive image analysis
        prompt = """
Please analyze this image thoroughly and provide the following information:
1. A detailed description of what's in the image
2. Main objects and elements present
3. Colors and visual attributes
4. Spatial relationships between objects
5. Any text visible in the image
6. Mood or atmosphere conveyed
7. Context or setting

Format your response as JSON with the following keys:
"description", "objects", "colors", "spatial_relationships", "text_content", "mood", "context"
"""
        
        try:
            # Read the image file
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                
            # Encode the image as base64
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare the messages with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # Make API call to GPT-4 Vision
            response = self._call_openai_api(
                "chat/completions",
                {
                    "messages": messages,
                    "model": "gpt-4-vision-preview",
                    "max_tokens": 1000,
                }
            )
            
            # Extract and parse the JSON response
            response_text = response['choices'][0]['message']['content'].strip()
            
            # Find the JSON portion using regex
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                analysis = json.loads(json_str)
                return analysis
            else:
                # If regex fails, try to parse the whole response as JSON
                try:
                    analysis = json.loads(response_text)
                    return analysis
                except:
                    # If JSON parsing fails, create a simple analysis with just the description
                    return {"description": response_text, "error": "Failed to parse JSON response"}
            
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return {"error": str(e)}
    
    def generate_log_connections(self, target_log: Dict[str, Any], other_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate meaningful connections between a target log and other logs.
        
        Args:
            target_log: The main log to find connections for
            other_logs: List of other logs to check for connections
            
        Returns:
            List of connected logs with connection descriptions
        """
        if not target_log or not other_logs:
            return []
        
        target_content = target_log.get('content', '')
        if not target_content:
            return []
        
        # Format the target and other logs
        target_time = ""
        if 'start_time' in target_log:
            try:
                dt = datetime.fromisoformat(target_log['start_time'])
                target_time = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        formatted_target = f"Log ID: {target_log.get('id', 'unknown')}\nTime: {target_time}\nContent: {target_content}"
        
        # Prepare a sample of other logs (limited to 10 to avoid API limits)
        sample_logs = other_logs[:10] if len(other_logs) > 10 else other_logs
        formatted_others = []
        
        for log in sample_logs:
            log_id = log.get('id', 'unknown')
            content = log.get('content', '')
            
            log_time = ""
            if 'start_time' in log:
                try:
                    dt = datetime.fromisoformat(log['start_time'])
                    log_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            formatted_others.append(f"Log ID: {log_id}\nTime: {log_time}\nContent: {content}")
        
        # Prepare the prompt
        prompt = f"""I have a main log entry and several other log entries. Please identify meaningful connections between the main log and each of the other logs.

MAIN LOG:
{formatted_target}

OTHER LOGS:
{'-' * 40}
{"".join([f"{i+1}. {log}\n{'-' * 40}\n" for i, log in enumerate(formatted_others)])}

For each other log that has a meaningful connection to the main log, provide:
1. The log ID
2. A brief description of the connection (type of relationship, common theme, etc.)
3. An explanation of how they relate
4. A relevance score from 0 to 1 (where 1 means highly relevant)

Format the response as a JSON array of objects, each with keys "log_id", "connection_type", "explanation", and "relevance_score".
Only include logs with genuine connections (relevance score > 0.3).
"""
        
        try:
            # Call the OpenAI API
            messages = [
                {"role": "system", "content": "You are an assistant that identifies meaningful connections between logs. response in a few lines."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_openai_api(
                "chat/completions",
                {
                    "messages": messages,
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 800,
                    "temperature": 0.5,
                }
            )
            
            # Extract and parse the JSON response
            response_text = response['choices'][0]['message']['content'].strip()
            
            # Find the JSON portion using regex
            json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                connections = json.loads(json_str)
                
                # Find the full log entries for connected logs
                result = []
                for connection in connections:
                    log_id = connection.get('log_id')
                    connected_log = next((log for log in other_logs if log.get('id') == log_id), None)
                    
                    if connected_log:
                        result.append({
                            "log": connected_log,
                            "connection_type": connection.get('connection_type', ''),
                            "explanation": connection.get('explanation', ''),
                            "relevance_score": connection.get('relevance_score', 0)
                        })
                
                return result
            else:
                # If JSON parsing fails, return empty list
                return []
            
        except Exception as e:
            print(f"Error generating log connections: {e}")
            return []
        
    def generate_memory_completion(self, memory_chunks: List[Dict[str, Any]], weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate a completed memory by enhancing and refining memory chunks based on weights.
        
        Args:
            memory_chunks: List of memory chunks
            weights: Mapping from memory ID to weight
            
        Returns:
            Generated complete memory text
        """
        if not memory_chunks:
            return ""
        
        # Sort memories by weight
        sorted_memories = sorted(
            [(memory, weights.get(memory.get('id', ''), 0.5)) for memory in memory_chunks],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Extract and format original memory content
        original_texts = []
        for memory, _ in sorted_memories:
            content = memory.get('content', '')
            if content:
                original_texts.append(f"**{content}**")
        
        original_combined = '\n\n'.join(original_texts)
        
        # Create system prompt
        system_prompt = """You are a memory enhancement system. Your task is to refine and enhance the user's memory content.
        Follow these rules:
        1. Prioritize maintaining the original memory structure, respecting event sequences.
        2. Improve the coherence and completeness of memories by filling gaps and clarifying ambiguous parts.
        3. It is acceptable to overwrite or adjust memories to ensure a logical and emotionally consistent narrative.
        4. Maintain the tone, voice, and style of the original content and replicate while enhancing it.
        5. Ensure smooth transitions between events without altering the sequence of memories.
        6. Ensure all original memory content remains enclosed within double asterisks (**). Do not remove the bold formatting.
        """
        
        # User prompt
        user_prompt = f"""Below are my original memory entries, ordered by importance. Enhance the clarity, link the memories and coherence of these memories by making adjustments as needed, but maintain the original sequence of events, feel free to make adjustment and make the content coherent, response in paragraphs:

    {original_combined}

    Note: Preserve the flow of events while making reasonable adjustments within each chunk to improve understanding and emotional accuracy. Keep the original text bolded using ** to indicate the exact keywords."""
        
        # Call OpenAI API
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self._call_openai_api(
                "chat/completions",
                {
                    "messages": messages,
                    "model": "gpt-4-turbo",
                    "max_tokens": 1500,
                    "temperature": 0.7,
                }
            )
            
            # Extract completed text
            completion = response['choices'][0]['message']['content'].strip()
            original_contents = [memory.get('content', '') for memory in memory_chunks]
            
            return {
                "completion": completion,
                "original_contents": original_contents
            }
            
        except Exception as e:
            print(f"Error generating memory completion: {e}")
            return {
                "completion": original_combined,
                "original_contents": original_contents
            }  # Return original content on failure
