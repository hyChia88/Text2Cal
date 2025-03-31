import os
import requests
import json
import random
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import openai
from dotenv import load_dotenv
import base64
import time
import re

# Load environment variables
load_dotenv()

class MemeGenerator:
    """
    A class to generate memes based on logs and labeled meme images.
    """
    
    def __init__(self, 
                 meme_images_dir: str, 
                 output_dir: str,
                 labels_file: str = "meme_labels.json",
                 openai_api_key: str = None):
        """
        Initialize the MemeGenerator.
        
        Args:
            meme_images_dir: Directory containing meme images
            output_dir: Directory for generated memes
            labels_file: JSON file to store/load image labels
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.meme_images_dir = meme_images_dir
        self.output_dir = output_dir
        self.labels_file = labels_file
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize OpenAI client
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("Warning: No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
        else:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Load existing labels if available
        self.image_labels = self._load_labels()
    
    def _load_labels(self) -> Dict[str, List[str]]:
        """
        Load image labels from the labels file.
        
        Returns:
            Dictionary mapping image filenames to their labels
        """
        if os.path.exists(self.labels_file):
            try:
                with open(self.labels_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding {self.labels_file}, starting with empty labels")
                return {}
        return {}
    
    def _save_labels(self) -> None:
        """
        Save image labels to the labels file.
        """
        with open(self.labels_file, 'w') as f:
            json.dump(self.image_labels, f, indent=2)
    
    def label_images(self, max_images: int = 50) -> None:
        """
        Label meme images using OpenAI's Vision model.
        
        Args:
            max_images: Maximum number of images to label
        """
        if not self.openai_api_key:
            print("Cannot label images: No OpenAI API key provided")
            return
        
        # Get list of image files
        image_files = [f for f in os.listdir(self.meme_images_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        
        # Shuffle and limit to max_images
        random.shuffle(image_files)
        image_files = image_files[:max_images]
        
        print(f"Starting to label {len(image_files)} images...")
        
        # Process each image
        for i, img_file in enumerate(image_files):
            if img_file in self.image_labels:
                print(f"Skipping already labeled image: {img_file}")
                continue
            
            img_path = os.path.join(self.meme_images_dir, img_file)
            
            try:
                # Read the image and convert to base64
                with open(img_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                print(f"Labeling image {i+1}/{len(image_files)}: {img_file}")
                
                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analyze this meme image and provide the following:\n1. A list of 5-10 descriptive keywords or labels that characterize the meme template (emotions, situations, characters, etc.)\n2. A brief description of what type of text/message this meme is typically used for\n\nFormat your response as a JSON object with keys 'labels' (array of strings) and 'description' (string)."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=800
                )
                
                # Extract and parse the JSON response
                response_text = response.choices[0].message.content
                
                # Find the JSON portion using regex
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Try to parse the entire response as JSON
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError:
                        # Create a basic structure if JSON parsing fails
                        result = {
                            "labels": ["meme", "unclassified"],
                            "description": "Failed to parse response"
                        }
                
                # Store the labels and description
                self.image_labels[img_file] = {
                    "labels": result.get("labels", []),
                    "description": result.get("description", "")
                }
                
                # Save after each successful labeling
                self._save_labels()
                
                # Be nice to the API and sleep a bit
                time.sleep(1)
                
            except Exception as e:
                print(f"Error labeling image {img_file}: {e}")
                # Don't stop on errors, continue with next image
        
        print(f"Completed labeling. Labeled {len(self.image_labels)} images total.")
    
    def extract_keywords_from_log(self, log_content: str) -> List[str]:
        """
        Extract relevant keywords from log content.
        
        Args:
            log_content: Text content of the log
            
        Returns:
            List of extracted keywords
        """
        if not self.openai_api_key:
            # Simple extraction method if no API key
            # Extract words that might be relevant for memes
            words = re.findall(r'\b[a-zA-Z]{3,}\b', log_content.lower())
            # Filter out common stop words
            stop_words = {'the', 'and', 'is', 'in', 'it', 'to', 'a', 'of', 'for', 'with'}
            return [word for word in words if word not in stop_words][:10]
        
        try:
            # Use OpenAI to extract keywords
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a keyword extraction assistant that identifies meme-worthy concepts."},
                    {"role": "user", "content": f"Extract 5-10 keywords from this text that would work well for finding a matching meme. Focus on emotions, situations, concepts and cultural references that appear in popular memes. Return ONLY a JSON array of strings with no explanation:\n\n{log_content}"}
                ],
                max_tokens=150,
                temperature=0.5
            )
            
            # Extract and parse the JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Find JSON list
            json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)
            if json_match:
                keywords = json.loads(json_match.group(1))
                return keywords
            else:
                # Try to parse the entire response
                try:
                    keywords = json.loads(response_text)
                    if isinstance(keywords, list):
                        return keywords
                except json.JSONDecodeError:
                    pass
            
            # Fallback to simple word extraction
            words = re.findall(r'\b[a-zA-Z]{3,}\b', log_content.lower())
            return [word for word in words if word not in {'the', 'and', 'is', 'in'}][:10]
            
        except Exception as e:
            print(f"Error extracting keywords from log: {e}")
            # Fallback to simple extraction
            words = re.findall(r'\b[a-zA-Z]{3,}\b', log_content.lower())
            return [word for word in words if word not in {'the', 'and', 'is', 'in'}][:10]
    
    def find_matching_meme(self, keywords: List[str]) -> str:
        """
        Find a meme image that matches the given keywords.
        
        Args:
            keywords: List of keywords to match
            
        Returns:
            Path to the selected meme image
        """
        if not self.image_labels:
            print("No labeled images available. Using a random image.")
            # Return a random image from the directory
            image_files = [f for f in os.listdir(self.meme_images_dir) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            if not image_files:
                raise ValueError("No meme images found in directory")
            return os.path.join(self.meme_images_dir, random.choice(image_files))
        
        # Calculate match scores for each labeled image
        match_scores = {}
        
        for img_file, img_data in self.image_labels.items():
            img_labels = img_data.get("labels", [])
            # Count how many keywords match with the image labels
            matches = sum(1 for kw in keywords if any(kw.lower() in label.lower() for label in img_labels))
            # Calculate match score based on number of matching keywords
            match_scores[img_file] = matches
        
        # Sort by match score (descending)
        sorted_matches = sorted(match_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get the top 3 matches
        top_matches = sorted_matches[:3]
        
        # If no good matches, pick randomly from all images
        if not top_matches or top_matches[0][1] == 0:
            print("No good matches found. Selecting randomly.")
            img_file = random.choice(list(self.image_labels.keys()))
        else:
            # Return the best match if score > 0, otherwise choose randomly from top 3
            if top_matches[0][1] > 0:
                img_file = top_matches[0][0]
            else:
                img_file = random.choice([m[0] for m in top_matches])
        
        return os.path.join(self.meme_images_dir, img_file)
    
    def generate_meme_text(self, log_content: str, meme_image: str) -> Dict[str, str]:
        """
        Generate appropriate meme text based on log content and selected image.
        
        Args:
            log_content: Text content of the log
            meme_image: Path to the selected meme image
            
        Returns:
            Dictionary with top_text and bottom_text
        """
        if not self.openai_api_key:
            # Simple text generation without API
            words = log_content.split()
            if len(words) <= 5:
                return {"top_text": log_content, "bottom_text": ""}
            
            mid_point = len(words) // 2
            return {
                "top_text": " ".join(words[:mid_point]),
                "bottom_text": " ".join(words[mid_point:])
            }
        
        # Get image metadata if available
        img_file = os.path.basename(meme_image)
        img_data = self.image_labels.get(img_file, {})
        img_description = img_data.get("description", "")
        
        # Read the image for API
        with open(meme_image, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meme generator assistant that creates appropriate text for meme templates based on user logs."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Create humorous meme text for this image based on the following log content:\n\n{log_content}\n\nImage description: {img_description}\n\nRespond with a JSON object with 'top_text' and 'bottom_text'. Keep text short and punchy (2-6 words each). Use standard meme capitalization and humor."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200
            )
            
            # Extract and parse the response
            response_text = response.choices[0].message.content
            
            # Find the JSON portion
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                meme_text = json.loads(json_match.group(1))
                return {
                    "top_text": meme_text.get("top_text", ""),
                    "bottom_text": meme_text.get("bottom_text", "")
                }
            else:
                # Try to parse the entire response
                try:
                    meme_text = json.loads(response_text)
                    return {
                        "top_text": meme_text.get("top_text", ""),
                        "bottom_text": meme_text.get("bottom_text", "")
                    }
                except json.JSONDecodeError:
                    # Manual parsing as fallback
                    top_text = ""
                    bottom_text = ""
                    if "top text:" in response_text.lower():
                        top_pattern = re.search(r'top text:?(.*?)(?:bottom text|$)', response_text, re.IGNORECASE | re.DOTALL)
                        if top_pattern:
                            top_text = top_pattern.group(1).strip()
                    
                    if "bottom text:" in response_text.lower():
                        bottom_pattern = re.search(r'bottom text:?(.*?)$', response_text, re.IGNORECASE | re.DOTALL)
                        if bottom_pattern:
                            bottom_text = bottom_pattern.group(1).strip()
                    
                    return {"top_text": top_text, "bottom_text": bottom_text}
        
        except Exception as e:
            print(f"Error generating meme text: {e}")
            # Fallback to simple text generation
            words = log_content.split()
            if len(words) <= 5:
                return {"top_text": log_content, "bottom_text": ""}
            
            mid_point = len(words) // 2
            return {
                "top_text": " ".join(words[:mid_point]),
                "bottom_text": " ".join(words[mid_point:])
            }
    
    def add_text_to_image(self, image_path: str, top_text: str, bottom_text: str) -> str:
        """
        Add top and bottom text to the meme image.
        
        Args:
            image_path: Path to the meme image
            top_text: Text for the top of the meme
            bottom_text: Text for the bottom of the meme
            
        Returns:
            Path to the generated meme image
        """
        # Open the image
        img = Image.open(image_path)
        
        # Create a drawing object
        draw = ImageDraw.Draw(img)
        
        # Determine font size based on image dimensions
        width, height = img.size
        font_size = int(height * 0.08)  # 8% of image height
        
        # Try to load a meme-friendly font, use default if not available
        try:
            font = ImageFont.truetype("Impact.ttf", font_size)
        except IOError:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Function to wrap text to fit image width
        def wrap_text(text, max_width):
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_width = draw.textlength(test_line, font=font)
                
                if test_width <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return lines
        
        # Wrap text to fit image width (80% of image width)
        max_width = width * 0.8
        top_lines = wrap_text(top_text.upper(), max_width)
        bottom_lines = wrap_text(bottom_text.upper(), max_width)
        
        # Add black outline function
        def draw_outlined_text(text, x, y, outline_size=2):
            # Draw outline
            for i in range(-outline_size, outline_size + 1):
                for j in range(-outline_size, outline_size + 1):
                    if i != 0 or j != 0:
                        draw.text((x + i, y + j), text, fill="black", font=font)
            
            # Draw text
            draw.text((x, y), text, fill="white", font=font)
        
        # Add top text
        y_position = height * 0.05  # 5% from top
        for line in top_lines:
            text_width = draw.textlength(line, font=font)
            x_position = (width - text_width) / 2
            draw_outlined_text(line, x_position, y_position)
            y_position += font_size * 1.2  # Move to next line
        
        # Add bottom text
        y_position = height * 0.85  # 15% from bottom
        for line in reversed(bottom_lines):  # Draw from bottom up
            y_position -= font_size * 1.2
            text_width = draw.textlength(line, font=font)
            x_position = (width - text_width) / 2
            draw_outlined_text(line, x_position, y_position)
        
        # Generate output filename
        output_filename = f"meme_{int(time.time())}.jpg"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Save the meme
        img.save(output_path, quality=95)
        
        return output_path
    
    def generate_meme_from_log(self, log_content: str) -> str:
        """
        Generate a meme based on log content.
        
        Args:
            log_content: Text content of the log
            
        Returns:
            Path to the generated meme
        """
        print(f"Generating meme for log: {log_content[:50]}...")
        
        # Extract keywords from log
        keywords = self.extract_keywords_from_log(log_content)
        print(f"Extracted keywords: {', '.join(keywords)}")
        
        # Find matching meme template
        meme_image = self.find_matching_meme(keywords)
        print(f"Selected meme template: {os.path.basename(meme_image)}")
        
        # Generate meme text
        meme_text = self.generate_meme_text(log_content, meme_image)
        print(f"Generated meme text: Top: '{meme_text['top_text']}', Bottom: '{meme_text['bottom_text']}'")
        
        # Create the meme
        output_path = self.add_text_to_image(meme_image, meme_text['top_text'], meme_text['bottom_text'])
        print(f"Meme generated and saved to: {output_path}")
        
        return output_path
    
    def display_top_matching_memes(self, keywords: List[str], num_memes: int = 5) -> List[str]:
        """
        Display the top matching meme templates for a set of keywords.
        
        Args:
            keywords: List of keywords to match
            num_memes: Number of top matching memes to display
            
        Returns:
            List of paths to the top matching meme templates
        """
        if not self.image_labels:
            print("No labeled images available.")
            return []
        
        # Calculate match scores
        match_scores = {}
        for img_file, img_data in self.image_labels.items():
            img_labels = img_data.get("labels", [])
            matches = sum(1 for kw in keywords if any(kw.lower() in label.lower() for label in img_labels))
            match_scores[img_file] = matches
        
        # Sort by match score (descending)
        sorted_matches = sorted(match_scores.items(), key=lambda x: x[1], reverse=True)
        top_matches = sorted_matches[:num_memes]
        
        # Print match information
        print(f"\nTop {num_memes} matching meme templates:")
        for i, (img_file, score) in enumerate(top_matches):
            img_data = self.image_labels.get(img_file, {})
            img_labels = img_data.get("labels", [])
            print(f"{i+1}. {img_file} (Score: {score})")
            print(f"   Labels: {', '.join(img_labels)}")
            print(f"   Description: {img_data.get('description', 'N/A')}")
        
        # Return paths to the top matching memes
        return [os.path.join(self.meme_images_dir, img_file) for img_file, _ in top_matches]