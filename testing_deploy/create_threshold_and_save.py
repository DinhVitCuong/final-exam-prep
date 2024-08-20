import os
from gpt_intergrate import generateAnalysis
import json
import time
# bay h, predict het accuracy cua tung type cau hoi tung chap ra, store vao 1 cho nao do
class createThreshold:
    def __init__(self, aim, subject, path):
        self.aim = aim
        self.subject = subject
        self.path = path
        self.chapter = int(path[-6])
        self.thres_th = 0
        self.thres_nb = 0
        self.thres_vd = 0
        self.thres_vdc = 0
    def percent_each_diff(self):
        with open(self.path, 'r', encoding = 'utf-8') as file:
            data = json.load(file)
        length = len(data)
        for entry in data:
            if entry["difficulty"] == 1:
                self.thres_th += 1
            elif entry["difficulty"] == 2:
                self.thres_nb += 1
            elif entry["difficulty"] == 3:
                self.thres_vd += 1
            elif entry["difficulty"] == 4:
                self.thres_vdc += 1
        return self.thres_nb/length, self.thres_th/length, self.thres_vd/length, self.thres_vdc/length
    def recommend_threshold(self):
        th, nb, vd, vdc = self.percent_each_diff()
        prompt = (f"Đối với môn học {self.subject} và chương {self.chapter} có các phân bổ câu hỏi như sau: \n"
                    f"Nhận biết: {nb*100}%\n"
                    f"Thông hiểu: {th*100}%\n"
                    f"Vận dụng: {vd*100}%\n"
                    f"Vận dụng cao: {vdc*100}%\n")
        prompt += (f"Với mục tiêu điểm là {self.aim} thì độ chính xác của các loại câu hỏi của user nên làm là bao nhiêu\n"
                    f"Không giải thích gì thêm, chỉ cần đưa ra số liệu cụ thể\n"
                    f"Ghi theo format sau: \n"
                    f"Nhận biết: ...\n"
                    f"Thông hiểu: ...\n"
                    f"Vận dụng: ...\n"
                    f"Vận dụng cao: ...\n"
                    f"nếu mục tiêu điểm lớn hơn 9.5 thì độ chính xác vận dụng cao >= 50% , còn lại thì độ chính xác vận dụng cao  < 50%")

        test = generateAnalysis("T")
        response = test.model.generate_content(prompt)
        return response.text

# file luu threshold nen la 1 file json
# math = {}
# for i in range(1, 8):
#     path = f"data/final_math/Math_C{i}.json"
#     test = createThreshold(9, "T", path)
#     time.sleep(10)
#     math[i] = test.recommend_threshold()
# with open("threshold_math.json", "w", encoding = 'utf-8') as file:
#     json.dump(math, file, ensure_ascii = False)


# physics = {}
# for i in range(1, 8):
#     path = f"data/Physics/Physics_C{i}.json"
#     test = createThreshold(9, "L", path)
#     physics[i] = test.recommend_threshold()
#     time.sleep(10)
# with open("threshold_physics.json", "w", encoding = 'utf-8') as file:
#     json.dump(physics, file, ensure_ascii = False)



# path = f"data/final_math/Math_C4.json"
# test = createThreshold(9, "T", path)
# print(test.recommend_threshold())