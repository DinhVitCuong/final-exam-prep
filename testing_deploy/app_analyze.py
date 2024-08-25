from gpt_intergrate import generateAnalysis, promptCreation
import json
# test2 = promptCreation("chapter",8, "T",3)
# print(test2.next_test_date())
test = generateAnalysis("T",3)

# print(test.analyze_progress())
# print(test.analyze_deep())
# print(test.detail_plan_and_timeline())

# with open("output.txt", "w", encoding="utf-8") as f:
#     f.write(test.detail_plan_and_timeline())



# Giả sử `test.format_data()` trả về chuỗi JSON



json_string = test.format_data()
if json_string.startswith("```json") and json_string.endswith("```"):
    json_string = json_string.strip("```json")
    json_string = json_string.strip("```")
print(json_string)
start_pos = json_string.find('[')
end_pos = json_string.find(']')

json_string = json_string[start_pos:end_pos+1]
# json_data = json.loads(json_string)
# print(json_data[0])

json_data = json.loads(json_string)
# Ghi dữ liệu vào file JSON
with open("todo_T.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)


