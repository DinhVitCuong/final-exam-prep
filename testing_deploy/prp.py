import json
import random
link = "T_chapter_results.json"
with open(link, 'r') as file:
    data = json.load(file)
def append_random_to_ids(id_list):
    return [f"{id}{random.randint(1, 4)}" for id in id_list]

# Process each entry in the data
for entry in data:
    if 'wrong_answers' in entry:
        entry['wrong_answers'] = append_random_to_ids(entry['wrong_answers'])
    if 'right_answers' in entry:
        entry['right_answers'] = append_random_to_ids(entry['right_answers'])
    if 'unchecked_answers' in entry:
        entry['unchecked_answers'] = append_random_to_ids(entry['unchecked_answers'])
    if 'time_spent_per_question' in entry:
        entry['time_spent_per_question'] = {f"{key}{random.randint(1, 4)}": value for key, value in entry['time_spent_per_question'].items()}

# Save the updated data
with open(link, 'w') as f:
    json.dump(data, f, indent=4)