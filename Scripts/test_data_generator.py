# Test script
import sys
sys.path.append('D:/ahYen Workspace/ahYen Work/Side projects/Text2Cal')
from backend.data_generator import DataGenerator
from backend.db_model import db

# Test with enhanced features
generator = DataGenerator(use_enhanced=True)
enhanced_count = generator.generate_and_load_to_db(db, num_samples=5, openai_ratio=0.5)
print(f"Generated {enhanced_count} enhanced records")

# Test with original features for comparison
generator = DataGenerator(use_enhanced=False)
original_count = generator.generate_and_load_to_db(db, num_samples=5)
print(f"Generated {original_count} original records")

# Fetch and print the most recent logs
recent_logs = db.get_logs(days=1)
for log in recent_logs:
    print(f"ID: {log['id']}")
    print(f"Content: {log['content']}")
    print(f"Tags: {log.get('tags', '')}")
    # print(f"Importance: {log.get('importance', '')}")
    print("-" * 50)