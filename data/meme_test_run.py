#!/usr/bin/env python3
"""
Test script for the Meme Generator system.
This script demonstrates the complete workflow from downloading images to generating memes from logs.
"""

import os
import json
import argparse
import requests
import zipfile
import io
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Ensure the MemeGenerator class is available
try:
    from meme_generator import MemeGenerator
except ImportError:
    print("MemeGenerator class not found. Make sure meme_generator.py is in the same directory.")
    exit(1)

def download_meme_dataset(url: str, output_dir: str, limit: int = 50) -> str:
    """
    Download and extract a dataset of meme images.
    
    Args:
        url: URL to download the dataset from
        output_dir: Directory to save the images
        limit: Maximum number of images to extract
        
    Returns:
        Path to the directory containing the extracted images
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Downloading dataset from {url}...")
    
    # For this test script, we'll simulate downloading by using sample images
    # In a real implementation, you would use:
    # response = requests.get(url)
    # with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
    #     zip_ref.extractall(output_dir)
    
    # Simulate dataset by creating placeholder images
    from PIL import Image, ImageDraw, ImageFont
    
    print(f"Creating {limit} placeholder meme templates...")
    
    # Create some sample meme templates
    templates = [
        {"name": "distracted_boyfriend", "width": 800, "height": 600, "bg_color": "lightblue", 
         "description": "A man looking at another woman while his girlfriend looks at him disapprovingly"},
        {"name": "drake", "width": 600, "height": 600, "bg_color": "lightyellow", 
         "description": "Drake refusing something and then approving something else"},
        {"name": "expanding_brain", "width": 600, "height": 800, "bg_color": "lightgreen", 
         "description": "Four panels showing increasingly elaborate or absurd ideas with expanding brain images"},
        {"name": "change_my_mind", "width": 800, "height": 500, "bg_color": "lightgray", 
         "description": "A person sitting at a table with a sign saying 'change my mind'"},
        {"name": "surprised_pikachu", "width": 600, "height": 600, "bg_color": "lightyellow", 
         "description": "Pikachu with a surprised expression"},
        {"name": "two_buttons", "width": 500, "height": 600, "bg_color": "lightpink", 
         "description": "Person sweating while deciding between two buttons"},
        {"name": "is_this_a_pigeon", "width": 700, "height": 500, "bg_color": "lightblue", 
         "description": "Anime character pointing at an object and asking if it's something completely different"},
        {"name": "doge", "width": 600, "height": 600, "bg_color": "lightyellow", 
         "description": "Shiba Inu dog with colorful text around it"},
        {"name": "success_kid", "width": 500, "height": 500, "bg_color": "lightgreen", 
         "description": "A toddler with a clenched fist expressing success"},
        {"name": "thinking_guy", "width": 600, "height": 600, "bg_color": "lightgray", 
         "description": "Person tapping their head with a knowing expression"}
    ]
    
    # Create placeholder images for the templates
    for i in range(min(limit, len(templates) * 5)):
        template = templates[i % len(templates)]
        img = Image.new('RGB', (template["width"], template["height"]), color=template["bg_color"])
        draw = ImageDraw.Draw(img)
        
        # Try to use a reasonable font size
        font_size = int(template["width"] * 0.05)
        try:
            font = ImageFont.truetype("Arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # Add template name and variant number
        variant = (i // len(templates)) + 1
        template_name = f"{template['name']}_v{variant}"
        
        # Draw template name at the top
        text_width = draw.textlength(template_name, font=font)
        position = ((template["width"] - text_width) // 2, 20)
        draw.text(position, template_name, fill=(0, 0, 0), font=font)
        
        # Draw a border to simulate the meme template structure
        draw.rectangle([(20, 60), (template["width"] - 20, template["height"] - 20)], 
                      outline=(0, 0, 0), width=2)
        
        # Save the image
        img_path = os.path.join(output_dir, f"{template_name}.jpg")
        img.save(img_path)
    
    print(f"Created {limit} meme templates in {output_dir}")
    return output_dir

def generate_synthetic_logs(num_logs: int = 20) -> List[Dict[str, Any]]:
    """
    Generate synthetic memory logs for testing.
    
    Args:
        num_logs: Number of logs to generate
        
    Returns:
        List of synthetic log dictionaries
    """
    # Sample log templates
    log_templates = [
        "Feeling {emotion} after my {activity} session today. {reaction}",
        "Just had a {adjective} meeting with {person}. We discussed {topic} and I'm feeling {emotion}.",
        "Spent the morning {activity}. {reaction} Now I need to {next_action}.",
        "Can't believe I {past_action}! {reaction}",
        "{emotion} about my progress on {project}. {detail}",
        "Today's {meal} was {adjective}. {reaction}",
        "Met with {person} to talk about {topic}. {detail}",
        "Tried a new {activity} technique today. {reaction} {next_action}",
        "My {project} deadline is approaching and I'm feeling {emotion}. {next_action}",
        "Had to deal with a {adjective} {problem} today. {reaction}",
    ]
    
    # Sample values for template placeholders
    emotions = ["excited", "worried", "motivated", "stressed", "proud", "frustrated", "inspired", "anxious", "relieved", "overwhelmed"]
    activities = ["workout", "coding", "writing", "reading", "meditation", "planning", "brainstorming", "hiking", "cooking", "drawing"]
    adjectives = ["productive", "challenging", "disappointing", "surprising", "inspiring", "frustrating", "enlightening", "exhausting", "boring", "fascinating"]
    people = ["my boss", "the team", "a client", "my mentor", "my colleague", "the project manager", "my partner", "a friend", "the consultant", "our investors"]
    topics = ["the new project", "our strategy", "budget concerns", "innovative ideas", "upcoming deadlines", "performance issues", "exciting opportunities", "technical challenges", "future plans", "process improvements"]
    reactions = ["I'm feeling good about it.", "Not sure what to think yet.", "It was better than expected!", "This is a game changer.", "I have mixed feelings about this.", "Could have gone better.", "Really happy with the outcome!", "Need to rethink my approach.", "Proud of what I accomplished.", "It was a complete disaster."]
    next_actions = ["focus on next steps", "take a break", "regroup and try again", "share the results", "get some feedback", "finalize the details", "present my findings", "improve the process", "delegate some tasks", "celebrate this win"]
    past_actions = ["forgot an important deadline", "solved that complex problem", "presented to the entire company", "learned a new skill", "made such a simple mistake", "received unexpected praise", "took on that challenging project", "stood up to that difficult situation", "changed my approach completely", "discovered a major issue"]
    projects = ["website redesign", "quarterly report", "product launch", "client proposal", "research paper", "marketing campaign", "app development", "budget planning", "training program", "data analysis"]
    details = ["The details are still coming together.", "It's more complex than I thought.", "We're making good progress.", "There are still some unresolved issues.", "The initial results look promising.", "We need more resources to complete it.", "The timeline is tight but doable.", "I'm excited about where this is heading.", "We need to pivot our approach.", "The feedback has been positive so far."]
    meals = ["breakfast", "lunch", "dinner", "snack", "coffee", "team meal", "client dinner", "quick bite", "home-cooked meal", "restaurant experience"]
    problems = ["technical issue", "misunderstanding", "conflict", "deadline", "resource constraint", "quality problem", "customer complaint", "unexpected delay", "budget cut", "scope change"]
    
    # Generate logs
    logs = []
    now = datetime.now()
    
    for i in range(num_logs):
        # Select a random template
        template = random.choice(log_templates)
        
        # Fill the template with random values
        content = template.format(
            emotion=random.choice(emotions),
            activity=random.choice(activities),
            adjective=random.choice(adjectives),
            person=random.choice(people),
            topic=random.choice(topics),
            reaction=random.choice(reactions),
            next_action=random.choice(next_actions),
            past_action=random.choice(past_actions),
            project=random.choice(projects),
            detail=random.choice(details),
            meal=random.choice(meals),
            problem=random.choice(problems)
        )
        
        # Generate a timestamp (within the last 30 days)
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        timestamp = (now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)).isoformat()
        
        # Create log entry
        log = {
            "id": f"log_{i+1}",
            "content": content,
            "start_time": timestamp,
            "importance": round(random.random(), 2)  # Random importance between 0 and 1
        }
        
        logs.append(log)
    
    return logs

def save_logs_to_file(logs: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save logs to a JSON file.
    
    Args:
        logs: List of log dictionaries
        output_file: Path to save the logs
    """
    with open(output_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    print(f"Saved {len(logs)} logs to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Test the Meme Generator with memory logs")
    parser.add_argument("--meme_dir", default="meme_images", help="Directory for meme images")
    parser.add_argument("--output_dir", default="generated_memes", help="Directory for generated memes")
    parser.add_argument("--logs_file", default="memory_logs.json", help="File to save synthetic logs")
    parser.add_argument("--num_logs", type=int, default=10, help="Number of synthetic logs to generate")
    parser.add_argument("--num_memes", type=int, default=3, help="Number of memes to generate")
    parser.add_argument("--skip_image_download", action="store_true", help="Skip downloading sample images")
    parser.add_argument("--use_openai", action="store_true", help="Use OpenAI for enhanced functionality")
    
    args = parser.parse_args()
    
    print("\n===== MEME GENERATOR TEST SCRIPT =====\n")
    
    # Step 1: Prepare directories
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Step 2: Download meme images if needed
    if not args.skip_image_download:
        print("\n=== STEP 1: Downloading meme templates ===\n")
        # In a real implementation, you would use a real URL
        # Example: "https://www.kaggle.com/datasets/hammadjavaid/6992-labeled-meme-images-dataset/download"
        download_meme_dataset(
            url="https://www.kaggle.com/datasets/hammadjavaid/6992-labeled-meme-images-dataset/download", 
            output_dir=args.meme_dir,
            limit=50
        )
    else:
        print(f"\n=== STEP 1: Using existing meme templates in {args.meme_dir} ===\n")
    
    # Step A: Check for meme images
    if not os.path.exists(args.meme_dir) or not os.listdir(args.meme_dir):
        print(f"Error: No meme images found in {args.meme_dir}. Please make sure the directory exists and contains images.")
        return
    
    # Step 3: Generate synthetic logs
    print(f"\n=== STEP 2: Generating {args.num_logs} synthetic memory logs ===\n")
    logs = generate_synthetic_logs(args.num_logs)
    save_logs_to_file(logs, args.logs_file)
    
    # Print sample logs
    print("\nSample logs:")
    for i, log in enumerate(logs[:3]):
        print(f"{i+1}. [{log['start_time']}] {log['content'][:80]}...")
    print(f"... and {len(logs) - 3} more logs\n")
    
    # Step 4: Initialize the MemeGenerator
    print("\n=== STEP 3: Initializing MemeGenerator ===\n")
    meme_gen = MemeGenerator(
        meme_images_dir=args.meme_dir,
        output_dir=args.output_dir
    )
    
    # Step 5: Label meme images (optional)
    if args.use_openai:
        print("\n=== STEP 4: Labeling meme images with OpenAI Vision ===\n")
        print("Note: This step requires an OpenAI API key with GPT-4 Vision access.")
        try:
            meme_gen.label_images(max_images=10)
        except Exception as e:
            print(f"Warning: Failed to label images with OpenAI. Error: {e}")
            print("Continuing with basic functionality...")
    else:
        # Create some basic labels manually for testing
        print("\n=== STEP 4: Creating basic meme labels for testing ===\n")
        labels = {}
        
        for img_file in os.listdir(args.meme_dir)[:20]:
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                template_name = os.path.splitext(img_file)[0]
                if "drake" in template_name.lower():
                    labels[img_file] = {
                        "labels": ["drake", "approve", "disapprove", "comparison", "preference", "choice"],
                        "description": "Drake refusing something and then approving something else"
                    }
                elif "distracted" in template_name.lower():
                    labels[img_file] = {
                        "labels": ["distracted", "boyfriend", "jealousy", "temptation", "preference", "choice"],
                        "description": "Man looking at another woman while his girlfriend looks at him disapprovingly"
                    }
                elif "brain" in template_name.lower():
                    labels[img_file] = {
                        "labels": ["expanding", "brain", "intelligence", "evolution", "progression", "absurd"],
                        "description": "Four panels showing increasingly elaborate ideas with expanding brain images"
                    }
                else:
                    labels[img_file] = {
                        "labels": ["meme", "funny", "reaction", template_name.split('_')[0]],
                        "description": f"Generic {template_name} meme template"
                    }
        
        meme_gen.image_labels = labels
        meme_gen._save_labels()
        print(f"Created basic labels for {len(labels)} meme templates")
    
    # Step 6: Generate memes from logs
    print(f"\n=== STEP 5: Generating {args.num_memes} memes from logs ===\n")
    
    # Select random logs to create memes from
    selected_logs = random.sample(logs, min(args.num_memes, len(logs)))
    
    generated_memes = []
    for i, log in enumerate(selected_logs):
        print(f"\nGenerating meme {i+1}/{len(selected_logs)} from log:")
        print(f"LOG: {log['content'][:100]}...")
        
        # Extract keywords from log
        keywords = meme_gen.extract_keywords_from_log(log['content'])
        print(f"Extracted keywords: {', '.join(keywords)}")
        
        # Display top matching memes
        print("\nFinding top matching meme templates...")
        matching_memes = meme_gen.display_top_matching_memes(keywords, num_memes=3)
        
        # Generate the meme
        print("\nGenerating meme...")
        meme_path = meme_gen.generate_meme_from_log(log['content'])
        generated_memes.append((log['content'], meme_path))
        print(f"Meme saved to: {meme_path}\n")
        print("-" * 60)
    
    # Step 7: Summary
    print("\n=== TEST RESULTS SUMMARY ===\n")
    print(f"Generated {len(generated_memes)} memes from logs:")
    for i, (log_content, meme_path) in enumerate(generated_memes):
        print(f"{i+1}. Log: {log_content[:50]}...")
        print(f"   Meme: {meme_path}")
    
    print(f"\nMeme images stored in: {args.output_dir}")
    print(f"Log data stored in: {args.logs_file}")
    
    print("\nTo view the generated memes, open the image files in your favorite image viewer.")
    print("\n===== TEST COMPLETED SUCCESSFULLY =====\n")

if __name__ == "__main__":
    main()