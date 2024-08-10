import json

class DrawChartBase:
    def __init__(self, subject_name, num_chap, test_type) -> None:
        self.subject_name = subject_name
        self.num_chap = num_chap
        self.test_type = test_type
    
    def load_data(self):
        try:
            with open(f'{self.subject_name}_{self.test_type}_results.json', 'r') as f:
                data = json.load(f)[-1]
                return data
        except FileNotFoundError:
            print(f"Warning: The file '{f'{self.subject_name}_{self.test_type}_results.json'}' was not found.")
            return None
    
    def cal_accu_diff(self):
        dic_right = {}
        dic_total = {}
        dic_ques = {}
        data = self.load_data()
        
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        
        with open(f"{self.subject_name}_test.json", 'r') as file:
            mock_test = json.load(file)
        
        if data is not None:
            for id in data.get("right_answers", []):
                matching_question = next((qa for qa in mock_db if qa["ID"] == id), None)
                if matching_question:
                    diff = matching_question["difficulty"]
                    if diff in dic_right:
                        dic_right[diff] += 1
                    else:
                        dic_right[diff] = 1
                    if diff in dic_ques:
                        dic_ques[diff].append(id)
                    else:
                        dic_ques[diff] = [id]
        
        for question in mock_test:
            diff = question["difficulty"]
            if diff in dic_total:
                dic_total[diff] += 1
            else:
                dic_total[diff] = 1
        
        accu_diff = {}
        for diff in dic_total:
            accu_diff[diff] = dic_right.get(diff, 0) / dic_total[diff] * 100
        
        return accu_diff, dic_ques, dic_total
    
    def lessons_id_to_review(self):
        data = self.load_data()
        lessons_review_dict = {}
        if data is not None:
            for id in data['wrong_answers']:
                chap = id[1:3]
                lesson = id[3:5]
                id_l = id[6:10]
                if chap in lessons_review_dict:
                    lessons_review_dict[chap]['lesson'].append(lesson)
                    lessons_review_dict[chap]['id_l'].append(id_l)
                else:
                    lessons_review_dict[chap] = {'lesson': [lesson], 'id_l': [id_l]}
        return lessons_review_dict

class DrawTotal(DrawChartBase):
    def cal_accu_chap(self, chap):
        data = self.load_data()
        score = 0
        
        if data is not None:
            for id in data["right_answers"]:
                if id[1:3] == str(chap).zfill(2):
                    score += 1
            if self.num_chap <= 2:
                num_ques = 15
            else:
                num_ques = 10
            return score / num_ques * 100
        return None
    
    def cal_time_chap(self, chap):
        data = self.load_data()
        time = 0
        if data is not None:
            for id in data["time_spent_per_question"]:
                if id[1:3] == str(chap).zfill(2):
                    time += data["time_spent_per_question"][id]
            return time
        return None
    
    def short_total_analysis(self):
        accu_chaps = []
        for chap in range(1, self.num_chap + 1):
            accu_chap = self.cal_accu_chap(chap)
            if accu_chap is not None:
                accu_chaps.append(accu_chap)
        
        time_chaps = []
        for chap in range(1, self.num_chap + 1):
            time_chap = self.cal_time_chap(chap)
            if time_chap is not None:
                time_chaps.append(time_chap)
        return accu_chaps, time_chaps
    
    def find_most_wrong_chap(self):
        accu_chaps, _ = self.short_total_analysis()
        if accu_chaps:
            return accu_chaps.index(min(accu_chaps)) + 1
    
    def difficult_percentile_per_chap(self):
        _, diff_ids, diff_nums = self.cal_accu_diff()
        chap_difficulty_count = {chap: {"TH": 0, "VD": 0, "VDC": 0} for chap in range(1, self.num_chap + 1)}
        chap_difficulty_percentile = {chap: {"TH": 0, "VD": 0, "VDC": 0} for chap in range(1, self.num_chap + 1)}
        
        for diff, ids in diff_ids.items():
            for id in ids:
                chap = int(id[1:3])
                chap_difficulty_count[chap][diff] += 1
        
        for chap in chap_difficulty_count:
            for diff in chap_difficulty_count[chap]:
                chap_difficulty_percentile[chap][diff] = chap_difficulty_count[chap][diff] / diff_nums[diff] * 100
        
        return chap_difficulty_percentile

class DrawChap(DrawChartBase):
    def difficult_percentile_per_chap(self):
        _, diff_ids, diff_nums = self.cal_accu_diff()
        chap_difficulty_count = {self.num_chap: {"TH": 0, "VD": 0, "VDC": 0}}
        chap_difficulty_percentile = {self.num_chap: {"TH": 0, "VD": 0, "VDC": 0}}
        
        for diff, ids in diff_ids.items():
            for id in ids:
                chap = int(id[1:3])
                chap_difficulty_count[chap][diff] += 1
        
        for chap in chap_difficulty_count:
            for diff in chap_difficulty_count[chap]:
                chap_difficulty_percentile[chap][diff] = chap_difficulty_count[chap][diff] / diff_nums[diff] * 100
        
        return chap_difficulty_percentile
    # This class can use methods directly from DrawChartBase
    pass

# For total analysis
# draw_total = DrawTotal("T", 3, "total")
# print(draw_total.short_total_analysis())
# print(draw_total.find_most_wrong_chap())
# print(draw_total.difficult_percentile_per_chap())

# # For chapter-specific analysis
draw_chap = DrawChap("T", 3, "chapter")
# print(draw_chap.cal_accu_diff())
print(draw_chap.lessons_id_to_review())
# print(draw_chap.difficult_percentile_per_chap())