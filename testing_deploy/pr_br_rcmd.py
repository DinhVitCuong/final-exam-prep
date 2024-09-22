# tu cac loai từ các chương, tên bài, loại bài (TH, NB , VD , VDC)
# 20 cau 1 turn, 15 cau dau on tap test tong, 5 cau sau on tap test chuong
# top 5 dang bai hay sai ben test total, top 3 dang bai hay sai ben test chuong
# test total thi lay 5 bai test gan nhat, test chuong thi lay 1 bai test gan nhan
import math
import json
import random

class pr_br_rcmd:
    def __init__(self, subject_name, n_total=1, n_chap=1):
        self.subject_name = subject_name
        self.n_total = n_total
        self.n_chap = n_chap
        self.top_t = []
        self.top_c = []
        self.chap_freq = {}
        self.aim = 9
        self.load_data()

    def load_data(self):
        try:
            # Load total results
            with open(f'{self.subject_name}_total_results.json', 'r') as f:
                data = json.load(f)[-self.n_total:]
                total_q = []
                count_t = {}

                # Process total results
                for i in range(self.n_total):
                    if data[i]["wrong_answers"] and data[i]["wrong_answers"][-1][-1] != '4':
                        total_q += data[i]["wrong_answers"]
                    if data[i]["unchecked_answers"] and data[i]["unchecked_answers"][-1][-1] != '4':
                        total_q += data[i]["unchecked_answers"]

                for i in total_q:
                    key = (i[:5], i[-1])
                    chapter = i[1:3]

                    if key in count_t:
                        count_t[key] += 1
                    else:
                        count_t[key] = 1

                    if chapter in self.chap_freq:
                        self.chap_freq[chapter] += 1
                    else:
                        self.chap_freq[chapter] = 1

                if len(count_t) >= 5:
                    self.top_t = sorted(count_t.items(), key=lambda x: x[1], reverse=True)[:5]
                else:
                    self.top_t = sorted(count_t.items(), key=lambda x: x[1], reverse=True)

                total_sum_all = sum(value for key, value in self.top_t)
                self.top_t = [(key, math.ceil((value / total_sum_all) * 15)) for key, value in self.top_t]

            # Load chapter results
            with open(f'{self.subject_name}_chapter_results.json', 'r') as f:
                data = json.load(f)[-self.n_chap:]
                chap_q = []
                count_c = {}

                # Process chapter results
                for i in range(self.n_chap):
                    if data[i]["wrong_answers"] and data[i]["wrong_answers"][-1][-1] != '4':
                        chap_q += data[i]["wrong_answers"]
                    if data[i]["unchecked_answers"] and data[i]["unchecked_answers"][-1][-1] != '4':
                        chap_q += data[i]["unchecked_answers"]

                for i in chap_q:
                    key = (i[:5], i[-1])
                    chapter = i[1:3]

                    if key in count_c:
                        count_c[key] += 1
                    else:
                        count_c[key] = 1

                    if chapter in self.chap_freq:
                        self.chap_freq[chapter] += 1
                    else:
                        self.chap_freq[chapter] = 1

                if len(count_c) >= 3:
                    self.top_c = sorted(count_c.items(), key=lambda x: x[1], reverse=True)[:3]
                else:
                    self.top_c = sorted(count_c.items(), key=lambda x: x[1], reverse=True)

                chapter_sum_all = sum(value for key, value in self.top_c)
                self.top_c = [(key, math.ceil((value / chapter_sum_all) * 5)) for key, value in self.top_c]

            # Sort chapter frequencies to find the top 2 chapters
            self.chap_freq = sorted(self.chap_freq.items(), key=lambda x: x[1], reverse=True)[:2]

        except FileNotFoundError as e:
            print(f"Warning: The file was not found: {str(e)}")
            return None

    def containter_type(self, id):  # Return a list of questions for each id
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]

        return [qa for qa in mock_db if qa["ID"][:5] == id[0][0] and qa["ID"][-1] == id[0][1]]
    def find_vdc(self,id_chap):  # Return a list of VDC questions
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        return [qa for qa in mock_db if qa["ID"][1:3] == id_chap and qa["difficulty"] == 4]
    def question_prep(self):  # Return a test with questions
        ques = []
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]

        for (id, _), num_id in self.top_t:
            matching_questions = [qa for qa in mock_db if qa["ID"][:5] == id]
            if len(matching_questions) >= num_id:
                ques += random.sample(matching_questions, num_id)
            else:
                ques += matching_questions  # Add all if not enough to sample

        for (id, _), num_id in self.top_c:
            matching_questions = [qa for qa in mock_db if qa["ID"][:5] == id]
            if len(matching_questions) >= num_id:
                ques += random.sample(matching_questions, num_id)
            else:
                ques += matching_questions  # Add all if not enough to sample

        # Adjust based on aim
        if self.aim >= 8.5 and self.aim < 9:
            # Insert logic to add VDC questions based on the top chapters in self.chap_freq
            # 1 vdc
            ques += random.sample(self.find_vdc(self.chap_freq[0][0]), 1)
        elif self.aim >= 9 and self.aim < 9.5:
            # 2 vdc
            ques += random.sample(self.find_vdc(self.chap_freq[0][0]), 1)
            ques += random.sample(self.find_vdc(self.chap_freq[1][0]), 1)
        elif self.aim >= 9.5:
            # 3 vdc
            ques += random.sample(self.find_vdc(self.chap_freq[0][0]), 2)
            ques += random.sample(self.find_vdc(self.chap_freq[1][0]), 1)
        else:
            pass
        return ques





test = pr_br_rcmd("T", 5)
print(test.question_prep())
