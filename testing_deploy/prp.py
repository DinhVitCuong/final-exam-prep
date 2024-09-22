import json
import random

hm = {
    "Thông hiểu" : 2,
    "Nhận biết" : 1,
    "Vận dụng" : 3,
    "Vận dụng cao" : 4
}

for i in range(1, 8):
    with open(f'data/final_math/Math_C{i}.json', 'r', encoding='utf-8') as f:
        datas = json.load(f)
        for data in datas:
            if data['difficulty'] not in hm.values():
                try:
                    data['difficulty'] = hm[data['difficulty']]
                    data['id'] = data['id'] + str(data['difficulty'])
                except KeyError:
                    print("Math")
                    print(i)
    # Save updated JSON file
    with open(f'data/final_math/Math_C{i}.json', 'w', encoding='utf-8') as f:
        json.dump(datas, f, ensure_ascii=False, indent=4)

# Update Physics JSON files
for i in range(1, 8):
    with open(f'data/Physics/Physics_C{i}.json', 'r', encoding='utf-8') as f:
        datas = json.load(f)
        for data in datas:
            if data['difficulty'] not in hm.values():
                try:
                    data['difficulty'] = hm[data['difficulty']]
                    data['id'] = data['id'] + str(data['difficulty'])
                except KeyError:
                    print("Physics")
                    print(i)
    # Save updated JSON file
    with open(f'data/Physics/Physics_C{i}.json', 'w', encoding='utf-8') as f:
        json.dump(datas, f, ensure_ascii=False, indent=4)
