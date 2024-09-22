import json
import random

# Generate 200 questions with chapter numbers from 1 to 5
# Generate 200 questions with chapter numbers from 1 to 5 in positions 2 and 3
questions = []
difficulty_levels = [1,2,3,4]

for i in range(1, 501):
    chapter = str(random.randint(1, 5)).zfill(2)
    difficulty = random.choice(difficulty_levels)
    question_id = f"T{chapter}{str(i // 100 + 1).zfill(2)}{str(i % 100).zfill(5)}"+str(difficulty)
    
    question = f"Question {i}"
    options = [f"Option A", f"Option B", f"Option C", f"Option D"]
    answer = random.choice(["A", "B", "C", "D"])
    explanation = f"Explanation {i}"
    
    questions.append({
        "ID": question_id,
        "difficulty": difficulty,
        "question": question,
        "images": "",
        "options": options,
        "answer": answer,
        "explain": explanation
    })

# Create the final JSON structure
data = {
    "QAs": questions
}



# Save to a JSON file
json_file_path = "T_mock.json"
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

json_file_path
