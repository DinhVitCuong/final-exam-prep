# tu cac loai từ các chương, tên bài, loại bài (TH, NB , VD , VDC)
# 20 cau 1 turn, 15 cau dau on tap test tong, 5 cau sau on tap test chuong
# top 5 dang bai hay sai ben test total, top 3 dang bai hay sai ben test chuong
# test total thi lay 5 bai test gan nhat, test chuong thi lay 1 bai test gan nhan
import math
import json
import random
class pr_br_rcmd:
    def __init__(self, subject_name, n_total = 1,n_chap = 1):
        self.subject_name = subject_name
        self.n_total = n_total
        self.n_chap = n_chap
        self.top_t = []
        self.top_c= []
        self.load_data()
    def load_data(self):
        try:
            with open(f'{self.subject_name}_total_results.json', 'r') as f:
                data = json.load(f)[-self.n_total:]
                total_q = []
                count_t = {}
                for i in range(self.n_total):
                    total_q += data[i]["wrong_answers"]
                    total_q += data[i]["unchecked_answers"]
                for i in total_q:
                    if i[:5] in count_t:
                        count_t[i[:5]] += 1
                    else:
                        count_t[i[:5]] = 1
                if len(count_t) >= 5:
                    self.top_t = sorted(count_t.items(), key=lambda x: x[1], reverse=True)[:5]
                else:
                    self.top_t = sorted(count_t.items(), key=lambda x: x[1], reverse=True)
                
                total_sum_all = sum(value for key, value in self.top_t)
    
                self.top_t = [(key, math.ceil((value / total_sum_all) * 15)) for key, value in self.top_t] 
            with open(f'{self.subject_name}_chapter_results.json', 'r') as f:
                data = json.load(f)[-self.n_chap:]
                chap_q = []
                count_c = {}
                for i in range(self.n_chap):
                    chap_q += data[i]["wrong_answers"]
                    chap_q += data[i]["unchecked_answers"]
                for i in chap_q:
                    if i[:5] in count_c:
                        count_c[i[:5]] += 1
                    else:
                        count_c[i[:5]] = 1
                if len(count_c) >= 3:
                    self.top_c = sorted(count_c.items(), key=lambda x: x[1], reverse=True)[:3]
                else:
                    self.top_c = sorted(count_c.items(), key=lambda x: x[1], reverse=True)
                chapter_sum_all = sum(value for key, value in self.top_c)
                self.top_c = [(key, math.ceil((value / chapter_sum_all) * 5)) for key, value in self.top_c] 
        except FileNotFoundError:
            print(f"Warning: The file '{f'{self.subject_name}_total_results.json'}' was not found.")
            return None
    def containter_type(self, id): # tra ve 1 list cac cau hoi cua tung id 
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        return [qa for qa in mock_db if qa["ID"][:5] == id]
    def question_prep(self): # tra ve 1 test cac cau hoi
        ques = []
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        for id,num_id in self.top_t:
            ques += random.sample([qa for qa in mock_db if qa["ID"][:5] == id],num_id)
        for id,num_id in self.top_c:
            ques += random.sample([qa for qa in mock_db if qa["ID"][:5] == id],num_id)
        return ques
    


test = pr_br_rcmd("T", 5)
print(test.question_prep())