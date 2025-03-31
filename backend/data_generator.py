import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import os
import re
from typing import List, Dict, Any, Optional

# Optional imports - will be used if available
try:
    from openai import OpenAI  # Import the new OpenAI client
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    pass  # Continue without dotenv

class DataGenerator:
    def __init__(self, use_enhanced=True, openai_api_key=None):
        """
        Initialize the DataGenerator with options for enhanced generation.
        
        Args:
            use_enhanced: Whether to use enhanced generation features when available
            openai_api_key: Optional OpenAI API key (will also check environment variable)
        """
        # Original topic lists (backward compatibility)
        self.topics = ["Study", "Project", "Meeting", "Research", 
                      "Course", "Reading", "Thinking", "Inspiration"]
        self.emotions = ["Excited", "Focused", "Confused", "Satisfied", 
                        "Tired", "Curious"]
        self.people = ["Professor", "Classmate", "Friend", "Mentor", 
                      "Team member"]
        self.locations = ["Library", "Lab", "Classroom", "Office", 
                         "Cafe", "Dorm"]
        
        # Enhanced generation settings
        self.use_enhanced = use_enhanced
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.openai_client = None
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
        
        # Initialize Faker if available
        self.faker = Faker() if FAKER_AVAILABLE else None
        
        # Enhanced topic lists (used when enhanced generation is enabled)
        if use_enhanced:
            # Initialize enhanced lists
            self._initialize_enhanced_lists()
    
    def _initialize_enhanced_lists(self):
        """Initialize enhanced topic and entity lists for more varied generation"""
        self.enhanced_topics = [
            "Machine Learning", "UX Design", "Data Visualization", 
            "Architecture", "Sustainable Design", "Digital Fabrication",
            "Computational Design", "Interactive Art", "Human-Computer Interaction",
            "Smart Cities", "Responsive Architecture", "Design Thinking"
        ] + self.topics  # Include original topics
        
        self.enhanced_emotions = [
            "Enthusiastic", "Focused", "Perplexed", "Satisfied", "Exhausted", 
            "Curious", "Inspired", "Frustrated", "Motivated", "Anxious", 
            "Confident", "Uncertain", "Hopeful", "Disappointed", "Excited"
        ] + self.emotions  # Include original emotions
        
        self.enhanced_people = [
            "Professor Johnson", "Dr. Kim", "Alex from the lab", 
            "Maya from design studio", "Team lead Sara", "Research advisor Daniel",
            "Classmate Noah", "Study partner Emma", "Project mentor Thomas",
            "Workshop instructor Olivia", "Department chair Dr. Parker"
        ] + self.people  # Include original people
        
        self.enhanced_locations = [
            "Design Studio", "Research Lab", "Fabrication Workshop", 
            "Conference Room B3", "East Campus Library", "Virtual Meeting",
            "Visualization Lab", "Maker Space", "Graduate Lounge", 
            "Robotics Lab", "Media Arts Center", "Innovation Hub"
        ] + self.locations  # Include original locations
        
        self.projects = [
            "Responsive Building Skin", "Urban Data Visualization", 
            "Interactive Installation", "Smart Material Research", 
            "Computational Form-Finding", "Sustainable Housing Prototype",
            "Digital Twin Development", "Virtual Reality Experience",
            "Parametric Facade System", "Robotic Fabrication Workflow"
        ]
        
        self.activities = [
            "brainstorming session", "literature review", "collecting data",
            "sketching concepts", "building prototype", "running experiments",
            "analyzing results", "preparing presentation", "code debugging", 
            "team meeting", "client feedback session", "progress review"
        ]
    
    def _generate_openai_log(self, prompt: str) -> Optional[str]:
        """Generate a log entry using OpenAI API (when available)"""
        if not OPENAI_AVAILABLE or not self.openai_client:
            return None
            
        try:
            # Using the new OpenAI client API format
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant creating realistic memory log entries for a design student or professional. Write in first person, keep it concise (1-3 sentences), detailed, and contextual."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error using OpenAI API: {e}")
            return None
    
    def _generate_structured_log(self, timestamp: datetime) -> str:
        """Generate a structured log entry with time/date format"""
        # Use enhanced lists if enabled
        topics_list = self.enhanced_topics if self.use_enhanced else self.topics
        people_list = self.enhanced_people if self.use_enhanced else self.people
        locations_list = self.enhanced_locations if self.use_enhanced else self.locations
        emotions_list = self.enhanced_emotions if self.use_enhanced else self.emotions
        
        topic = random.choice(topics_list)
        person = random.choice(people_list)
        location = random.choice(locations_list)
        emotion = random.choice(emotions_list)
        
        # Different log structure types (only in enhanced mode)
        if self.use_enhanced:
            structure_type = random.choice(["dated_with_time", "dated_range", "basic_dated"])
            project = random.choice(self.projects)
            activity = random.choice(self.activities)
            
            if structure_type == "dated_with_time":
                # Format: @Month Day, Year 12pm-2pm Activity
                hour = random.randint(8, 18)  # Between 8am and 6pm
                duration = random.randint(1, 3)  # 1-3 hours
                
                date_str = timestamp.strftime("%B %d, %Y")
                start_time = f"{hour}{'pm' if hour >= 12 else 'am'}"
                end_time = f"{(hour + duration) % 12 or 12}{'pm' if hour + duration >= 12 else 'am'}"
                
                log = f"@{date_str} {start_time}-{end_time} {activity} for {project}"
                
                # Add location and/or people sometimes
                if random.random() > 0.5:
                    log += f" at {location}"
                
                if random.random() > 0.6:
                    log += f" with {person}"
                    
                # Add note or emotion at the end sometimes
                if random.random() > 0.7:
                    log += f". Feeling {emotion.lower()} about our progress."
                    
            elif structure_type == "dated_range":
                # Format: @2023-05-15 to 2023-05-20 Project phase description
                end_date = timestamp + timedelta(days=random.randint(2, 14))
                date_format = random.choice(["%Y-%m-%d", "%m/%d/%Y"])
                
                log = f"@{timestamp.strftime(date_format)} to {end_date.strftime(date_format)} "
                log += f"Working on {project} - "
                
                phase_descriptions = [
                    f"research phase exploring {topic}",
                    f"prototyping solutions for {topic}",
                    f"finalizing the {random.choice(self.activities)} stage",
                    f"iterating on design based on feedback from {person}",
                    f"documentation and presentation preparation"
                ]
                log += random.choice(phase_descriptions)
                
            else:  # basic_dated
                # Format: @May 15, 2023 Simple project update
                date_str = timestamp.strftime("%B %d, %Y")
                log = f"@{date_str} "
                
                update_templates = [
                    f"Made progress on {project}. {random.choice(self.activities).capitalize()} went well.",
                    f"Hit a roadblock with {topic} implementation. Need to consult with {person}.",
                    f"Breakthrough moment working on {project}! The {random.choice(self.activities)} yielded unexpected results.",
                    f"Reviewed literature on {topic} for {project}. Found some promising approaches.",
                    f"Planning next steps for {project}. Feeling {emotion.lower()} about the direction."
                ]
                log += random.choice(update_templates)
        else:
            # Original implementation (backward compatibility)
            content = f"@{timestamp.strftime('%m/%d/%Y')} "
            
            with_person = random.random() > 0.6
            add_location = random.random() > 0.5
            
            if with_person:
                content += f"with {person} "
            if add_location:
                content += f"at {location} "
                
            content += f"discussing {topic}, feeling {emotion}."
            log = content
        
        return log
    
    def _generate_diary_entry(self, timestamp: datetime, use_openai: bool = True) -> str:
        """Generate a more natural diary-style entry"""
        # Try OpenAI if enabled and available
        if use_openai and self.use_enhanced and OPENAI_AVAILABLE and self.openai_client:
            # Use enhanced topics if available
            topics_list = self.enhanced_topics if self.use_enhanced else self.topics
            project = random.choice(self.projects) if self.use_enhanced else random.choice(topics_list)
            emotion = random.choice(self.enhanced_emotions if self.use_enhanced else self.emotions)
            
            # Craft prompt for OpenAI
            prompt_templates = [
                f"Write a short diary entry about feeling {emotion} while working on a {topics_list[0]} project. Include specific details.",
                f"Write a brief reflection on recent progress with my {project} project. Mention challenges and thoughts.",
                f"Create a short personal note about insights gained while studying {topics_list[1]} today. Include how it connects to my work.",
                f"Write a concise diary entry about a collaboration with colleagues on {project}. Express how I feel about it.",
                f"Create a brief personal reflection about balancing multiple projects including {project} and research on {topics_list[2]}."
            ]
            
            prompt = random.choice(prompt_templates)
            entry = self._generate_openai_log(prompt)
            
            if entry:
                return entry
                
        # Fallback to template-based generation
        # Use enhanced lists if enabled 
        topics_list = self.enhanced_topics if self.use_enhanced else self.topics
        people_list = self.enhanced_people if self.use_enhanced else self.people
        emotions_list = self.enhanced_emotions if self.use_enhanced else self.emotions
        
        topic = random.choice(topics_list)
        emotion = random.choice(emotions_list)
        person = random.choice(people_list)
        
        # Enhanced template-based generation
        if self.use_enhanced and self.faker:
            project = random.choice(self.projects)
            
            templates = [
                f"Today I explored new concepts related to {topic}. {self.faker.sentence()} I'm feeling {emotion.lower()} about the possibilities this opens up for {project}.",
                
                f"Spent the morning thinking about {project}. {self.faker.sentence()} The challenge of {self.faker.word()} is both frustrating and exciting. Feeling {emotion.lower()} overall.",
                
                f"Had an interesting conversation with {person} about {topic}. Their perspective on {self.faker.word()} made me reconsider my approach to {project}. {self.faker.sentence()}",
                
                f"Reflecting on the past week of work on {project}. {self.faker.sentence()} Despite the challenges with {self.faker.word()}, I'm {emotion.lower()} about where things are heading.",
                
                f"Finding it difficult to focus on {topic} research today. {self.faker.sentence()} Maybe I need to change my environment or take a different angle on {project}.",
                
                f"Made a breakthrough on {project} this afternoon! The connection between {topic} and {self.faker.word()} wasn't obvious until now. Feeling {emotion.lower()} about this development."
            ]
            
            return random.choice(templates)
        else:
            # Original implementation (backward compatibility)
            return f"Today I thought about {topic}. I feel {emotion}, hoping for a breakthrough."
    
    def generate_synthetic_dataset(self, num_samples=500, output_file=None, openai_ratio=0.3):
        """Generate a synthetic memory dataset with varied, realistic entries"""
        # Generate date range (past 90 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        data = []
        for i in range(num_samples):
            # Random timestamp
            timestamp = start_date + (end_date - start_date) * random.random()
            
            # Determine log type
            use_openai = random.random() < openai_ratio and OPENAI_AVAILABLE and self.openai_client
            
            if random.random() > 0.4 or not self.use_enhanced:  # 60% logs, 40% diary
                content = self._generate_structured_log(timestamp)
                log_type = "structured" if self.use_enhanced else "log"
            else:
                content = self._generate_diary_entry(timestamp, use_openai=use_openai)
                log_type = "diary"
            
            # Metadata and categorization
            if self.use_enhanced:
                if random.random() > 0.8:  # 20% chance of having multiple tags
                    tag_count = random.randint(2, 4)
                    tag_pool = (self.enhanced_topics + 
                               [t.lower() for t in self.enhanced_emotions])
                    tags = random.sample(tag_pool, tag_count)
                else:
                    tags = [random.choice(self.enhanced_topics)]
                    
                # Category based on content
                if "meeting" in content.lower() or "session" in content.lower():
                    category = "Meeting"
                elif "research" in content.lower() or "study" in content.lower():
                    category = "Research"
                elif "prototype" in content.lower() or "build" in content.lower():
                    category = "Prototype"
                elif "idea" in content.lower() or "concept" in content.lower():
                    category = "Idea"
                elif "planning" in content.lower() or "schedule" in content.lower():
                    category = "Planning"
                else:
                    category = random.choice(["Task", "Note", "General"])
            else:
                # Original implementation (backward compatibility)
                tags = random.sample(self.topics + self.emotions, random.randint(1, 3))
                category = random.choice(["Meeting", "Task", "Idea", "Note", "Research", "General"])
            
            # Generate end_time for scheduled items
            has_time_range = "-" in content and any(x in content for x in ["am", "pm"])
            end_time = None
            if has_time_range:
                end_time = (timestamp + timedelta(hours=random.randint(1, 3))).isoformat()
            
            # Add importance based on keywords (enhanced)
            importance = 0.5  # default importance
            if self.use_enhanced:
                high_importance_words = ["urgent", "critical", "deadline", "important", "crucial", "key"]
                if any(word in content.lower() for word in high_importance_words):
                    importance = random.uniform(0.7, 1.0)
                elif "maybe" in content.lower() or "consider" in content.lower() or "might" in content.lower():
                    importance = random.uniform(0.3, 0.5)
            else:
                # Original importance (backward compatibility)
                importance = round(random.random() * 0.7 + 0.3, 2)  # 0.3-1.0 range
                
            # Add to dataset
            data.append({
                "id": str(i),
                "content": content,
                "start_time": timestamp.isoformat(),
                "end_time": end_time,
                "category": category,
                "tags": ",".join(tags),
                "importance": round(importance, 2),
                "type": log_type,
                "openai_generated": use_openai and log_type == "diary" if self.use_enhanced else False
            })
        
        # Create semantic connections between related memories (enhanced)
        if self.use_enhanced:
            self._create_memory_connections(data)
        
        # Create a DataFrame
        df = pd.DataFrame(data)
        
        # Save to file if specified
        if output_file:
            df.to_csv(output_file, index=False)
            
        return df
    
    def _create_memory_connections(self, data):
        """
        Create memory connections to ensure some memories are semantically related.
        (Enhanced feature - only used when use_enhanced=True)
        """
        if not self.use_enhanced:
            # Original implementation (backward compatibility)
            # Modify 10% of the memories to create connections
            for i in range(len(data) // 10):
                source_idx = random.randint(0, len(data) - 3)
                source_memory = data[source_idx]
                
                # Extract topics or emotions
                words = source_memory["content"].split()
                topic = random.choice(self.topics)
                emotion = random.choice(self.emotions)
                
                for topic_word in self.topics:
                    if topic_word in source_memory["content"]:
                        topic = topic_word
                        break
                        
                for emotion_word in self.emotions:
                    if emotion_word in source_memory["content"]:
                        emotion = emotion_word
                        break
                
                # Create 1-2 follow-up memories
                for j in range(random.randint(1, 2)):
                    follow_idx = source_idx + j + 1
                    if follow_idx < len(data):
                        timestamp = datetime.fromisoformat(source_memory["start_time"]) + timedelta(days=random.randint(1, 7))
                        
                        if random.random() > 0.5:
                            content = f"@{timestamp.strftime('%m/%d/%Y')} Continuing research on {topic}, " + \
                                    f"feeling {emotion}. Made new discoveries."
                        else:
                            content = f"Thinking back to the discussion about {topic} from a few days ago, I feel we need to explore it deeper."
                        
                        # Update the memory
                        data[follow_idx]["content"] = content
                        data[follow_idx]["start_time"] = timestamp.isoformat()
                        
                        # Add the topic to tags
                        tags = data[follow_idx]["tags"].split(",")
                        if topic not in tags:
                            tags.append(topic)
                        data[follow_idx]["tags"] = ",".join(tags)
            return
                        
        # Enhanced implementation for memory connections
        # For 20% of memories, create follow-up entries
        for i in range(len(data) // 5):
            # Select a random source memory
            source_idx = random.randint(0, len(data) - 3)
            source_memory = data[source_idx]
            
            # Extract key topics/projects from content
            content_words = source_memory["content"].lower().split()
            
            # Find topics or projects mentioned
            identified_topics = []
            for topic in self.enhanced_topics:
                if topic.lower() in source_memory["content"].lower():
                    identified_topics.append(topic)
                    
            for project in self.projects:
                if project.lower() in source_memory["content"].lower():
                    identified_topics.append(project)
            
            # If no topics found, use a random one
            if not identified_topics:
                identified_topics = [random.choice(self.enhanced_topics)]
                
            # Create 1-2 related follow-up memories
            for j in range(random.randint(1, 2)):
                follow_idx = source_idx + j + 1
                if follow_idx < len(data):
                    # Create timestamp a few days later
                    timestamp = datetime.fromisoformat(source_memory["start_time"]) + timedelta(days=random.randint(1, 7))
                    
                    # Generate follow-up content
                    chosen_topic = random.choice(identified_topics)
                    
                    if random.random() > 0.5 and OPENAI_AVAILABLE and self.openai_client:
                        # Use OpenAI for a more natural follow-up
                        prompt = f"Write a short follow-up diary entry that references previous work on {chosen_topic}. Start with something like 'Following up on' or 'Continuing with' or 'After our previous discussion about'. Keep it under 100 words."
                        follow_up = self._generate_openai_log(prompt)
                        if follow_up:
                            content = follow_up
                        else:
                            content = f"Following up on {chosen_topic} from last week. Made some progress with the concepts we discussed. Need to refine the approach further."
                    else:
                        # Template-based follow-up
                        if self.faker:
                            templates = [
                                f"Following up on our {chosen_topic} discussion from {random.choice(['earlier', 'last week', 'our meeting'])}. {self.faker.sentence()} Next steps: {self.faker.sentence()}",
                                
                                f"Continuing work on {chosen_topic}. Building on previous insights, I've {random.choice(['discovered', 'implemented', 'explored'])} {self.faker.word()}. {self.faker.sentence()}",
                                
                                f"After our previous session on {chosen_topic}, I've been thinking about {self.faker.sentence()} This connects to our earlier work through {self.faker.word()}.",
                                
                                f"@{timestamp.strftime('%B %d, %Y')} Follow-up meeting about {chosen_topic}. Reviewed progress since last discussion and identified next action items."
                            ]
                        else:
                            templates = [
                                f"Following up on our {chosen_topic} discussion from last week. Made some progress with the concepts. Next steps: continue research.",
                                
                                f"Continuing work on {chosen_topic}. Building on previous insights, I've discovered some interesting patterns.",
                                
                                f"After our previous session on {chosen_topic}, I've been thinking about new approaches. This connects to our earlier work.",
                                
                                f"@{timestamp.strftime('%B %d, %Y')} Follow-up meeting about {chosen_topic}. Reviewed progress since last discussion."
                            ]
                            
                        content = random.choice(templates)
                    
                    # Update the follow-up memory
                    data[follow_idx]["content"] = content
                    data[follow_idx]["start_time"] = timestamp.isoformat()
                    
                    # Add the topic to tags to strengthen connection
                    tags = data[follow_idx]["tags"].split(",")
                    topic_to_add = chosen_topic.lower().replace(" ", "-")
                    if topic_to_add not in tags:
                        tags.append(topic_to_add)
                    data[follow_idx]["tags"] = ",".join(tags)
                    
                    # Mark as a follow-up (for enhanced metadata)
                    data[follow_idx]["is_follow_up"] = True
                    if "source_memory_id" not in data[follow_idx]:
                        data[follow_idx]["source_memory_id"] = source_memory["id"]
    
    def generate_and_load_to_db(self, db, num_samples=500, openai_ratio=0.3):
        """Generate data and directly load to database"""
        print(f"Generating {num_samples} synthetic memory records...")
        df = self.generate_synthetic_dataset(num_samples, openai_ratio=openai_ratio)
        
        # Save to file for debugging/review
        output_path = "synthetic_memories.json"
        try:
            # Convert to JSON and save
            json_data = df.to_json(orient="records", indent=2)
            with open(output_path, 'w') as f:
                f.write(json_data)
            print(f"Synthetic data saved to {output_path}")
        except Exception as e:
            print(f"Error saving synthetic data to file: {e}")
        
        # Add to database
        successful_count = 0
        for _, row in df.iterrows():
            try:
                db.add_log(
                    content=row["content"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    tags=row["tags"],
                    importance=row["importance"]
                )
                successful_count += 1
            except Exception as e:
                print(f"Error adding record to database: {e}")
                
        print(f"Successfully added {successful_count} records to the database")
        return successful_count


if __name__ == "__main__":
    # Create an instance of the generator
    # With enhanced features disabled (original behavior)
    original_generator = DataGenerator(use_enhanced=False)
    print("Generating with original features...")
    original_df = original_generator.generate_synthetic_dataset(num_samples=5, output_file="original_sample.csv")
    
    # With enhanced features enabled
    print("\nGenerating with enhanced features...")
    enhanced_generator = DataGenerator(use_enhanced=True)
    enhanced_df = enhanced_generator.generate_synthetic_dataset(num_samples=5, output_file="enhanced_sample.csv")
    
    print("\nOriginal sample:")
    print(original_df[['content', 'type']])
    
    print("\nEnhanced sample:")
    print(enhanced_df[['content', 'type']])