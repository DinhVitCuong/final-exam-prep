from gpt_intergrate import generateAnalysis, promptCreation
import json

test = generateAnalysis("T",3)
# "deep", "fast", "progress", "chapter"
# print(test.analyze("deep"))

def turning_into_json(json_string):
    start_pos = json_string.find("[")
    end_pos = json_string.find("]")
    json_string = json_string[start_pos:end_pos+1]
    json_data = json.loads(json_string)
    return json_data

stringg = test.format_data()
with open("todo_T.txt", "w", encoding="utf-8") as f:
    f.write(stringg)
json_data = turning_into_json(stringg)
with open("todo_T.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)


