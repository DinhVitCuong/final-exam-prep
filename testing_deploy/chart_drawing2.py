import json
import os
import google.generativeai as genai
import pandas as pd 
# chủ yếu lấy ra từng vòng lặp 
class DrawChartBase:
    def __init__(self, subject_name, num_chap, test_type, num, load_type = None, ) -> None:
        self.subject_name = subject_name
        self.num_chap = num_chap
        self.test_type = test_type
        self.num = num
        self.load_type = load_type if load_type in ["specific", "average"] else None
        self.time_to_do_test = None
        self.load_data()
        self.date_and_time_calc("2024-08-23", "2025-06-27", 9)
    def load_data(self):
        try:
            if self.load_type == None or self.load_type == "average":
                with open(f'{self.subject_name}_{self.test_type}_results.json', 'r') as f:
                    if self.test_type == "total":
                        data = json.load(f)[-self.num:]
                        self.num_chap = max(int(data2["chapter"]) for data2 in data)
                        return data
                    elif self.test_type == "chapter":
                        all_tests = json.load(f)
                        chapter_tests = [test for test in all_tests if int(test["chapter"]) == self.num_chap]
                        
                        num_tests_to_return = min(len(chapter_tests), self.num)
                        return chapter_tests[-num_tests_to_return:]
                return data
            else:
                with open(f'{self.subject_name}_{self.test_type}_results.json', 'r') as f:
                    if self.test_type == "total":
                        data = [json.load(f)[self.num]]
                        self.num_chap = data[0]["chapter"]
                        self.time_to_do_test = 1
                        return data
                    elif self.test_type == "chapter":
                        data = [json.load(f)[self.num]]
                        self.num_chap = data[0]["chapter"]
                        self.time_to_do_test = 0.5
                        return data
            
        except FileNotFoundError:
            print(f"Warning: The file '{f'{self.subject_name}_{self.test_type}_results.json'}' was not found.")
            return None
    def cal_accu_diff(self):
        dic_right = {}
        dic_total = {}
        dic_ques = {}
        datas = self.load_data()
        for data in datas:
            with open(f"{self.subject_name}_mock.json", 'r') as file:
                mock_db = json.load(file)["QAs"]
            mock_test = data.get("right_answers", []) + data.get("wrong_answers", []) + data.get("unchecked_answers", [])
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
            for id in mock_test:
                diff = int(id[-1])
                if diff in dic_total:
                    dic_total[diff] += 1
                else:
                    dic_total[diff] = 1

        accu_diff = {}
        for diff in dic_total:
            accu_diff[diff] = dic_right.get(diff, 0) / dic_total[diff] * 100
        
        for i in range(1,5):
            if i not in dic_total:
                dic_total[i] = 0
        return accu_diff, dic_ques, dic_total # accuracy per diff (để vẽ accuracy giữa các độ khó), list right ID per diff , total number of question per diff
    def lessons_id_to_review(self): # lấy ra các bài học cần ôn tập
        datas = self.load_data()
        lessons_review_dict = {}
        for data in datas:
            if data is not None:
                for id in data['wrong_answers']:
                    chap = id[1:3]
                    lesson = id[3:5]
                    id_l = id[6:11]
                    
                    if chap in lessons_review_dict:
                        # Check if the lesson already exists for this chapter
                        if lesson in lessons_review_dict[chap]['lesson']:
                            lessons_review_dict[chap]['lesson'][lesson] += 1
                        else:
                            lessons_review_dict[chap]['lesson'][lesson] = 1
                        lessons_review_dict[chap]['id_l'].append(id_l)
                    else:
                        # Initialize the chapter with the lesson and id_l
                        lessons_review_dict[chap] = {'lesson': {lesson: 1}, 'id_l': [id_l]}
                for id in data['unchecked_answers']:
                    chap = id[1:3]
                    lesson = id[3:5]
                    id_l = id[6:11]
                    
                    if chap in lessons_review_dict:
                        # Check if the lesson already exists for this chapter
                        if lesson in lessons_review_dict[chap]['lesson']:
                            lessons_review_dict[chap]['lesson'][lesson] += 1
                        else:
                            lessons_review_dict[chap]['lesson'][lesson] = 1
                        lessons_review_dict[chap]['id_l'].append(id_l)
                    else:
                        # Initialize the chapter with the lesson and id_l
                        lessons_review_dict[chap] = {'lesson': {lesson: 1}, 'id_l': [id_l]}
        for chap in lessons_review_dict:
            # lessons_review_dict[chap]['lesson'] = list(set(lessons_review_dict[chap]['lesson']))
            lessons_review_dict[chap]['id_l'] = list(set(lessons_review_dict[chap]['id_l']))
        
        # trung binh self.num lan thi so cau sai cua cac bai hoc la 
        for chap in lessons_review_dict:
            lessons_review_dict[chap]['lesson'] = {k: v/self.num for k, v in lessons_review_dict[chap]['lesson'].items()}
        return lessons_review_dict
    def previous_results(self): 
        results = []
        durations = []
        exact_time = []
        num_quess = []
        datas = self.load_data()
        for a in datas:
            num_ques = a["total_questions"]
            num_quess.append(num_ques)
            duration = 0
            results.append(a['score'])
            for time in a['time_spent_per_question'].values():
                duration += time
            durations.append(duration)
            exact_time.append(a["completion_time"])
        return results, durations, exact_time,  num_quess # list of scores, list of durations, list of exact time
    def date_and_time_calc(self,start_date, final_date, aim):
        # 7 chapter
        final_date = pd.to_datetime(final_date)
        start_date = pd.to_datetime(start_date)
        if aim >= 9:
            prep_time = 5 # months
        elif aim >= 8:
            prep_time = 3
        else:
            prep_time = 1
        get_date_prep = final_date - pd.DateOffset(months=prep_time)
        if self.test_type == "total":
            self.time_to_do_test = (get_date_prep - start_date)/7
        elif self.test_type == "chapter":
            self.time_to_do_test = (get_date_prep - start_date)/14
        return get_date_prep

class DrawTotal(DrawChartBase):
    def cal_accu_chap(self, chap):
        datas = self.load_data()
        scores = []
        for data in datas:
            score = 0
            if data is not None:
                for id in data["right_answers"]:
                    if id[1:3] == str(chap).zfill(2):
                        score += 1
                if self.num_chap <= 2:
                    num_ques = 15
                else:
                    num_ques = 10
            scores.append(score / num_ques * 100)
        return sum(scores) / self.num
    
    def cal_time_chap(self, chap):
        datas = self.load_data()
        times = []
        for data in datas:
            time = 0
            if data is not None:
                for id in data["time_spent_per_question"]:
                    if id[1:3] == str(chap).zfill(2):
                        time += data["time_spent_per_question"][id]
            times.append(time)
        return sum(times) / self.num
    
    def short_total_analysis(self):
        accu_chaps = {}
        time_chaps = {}
        
        # Collect accuracy and time data for each chapter
        for chap in range(1, self.num_chap + 1):
            time_chap = self.cal_time_chap(chap)
            accu_chap = self.cal_accu_chap(chap)

            # Initialize lists for each chapter if they don't exist
            if chap not in accu_chaps:
                accu_chaps[chap] = []
            if chap not in time_chaps:
                time_chaps[chap] = []

            # Append the accuracy and time data to the respective lists
            if accu_chap is not None:
                accu_chaps[chap].append(accu_chap)
            if time_chap is not None:
                time_chaps[chap].append(time_chap)

        # Calculate the average accuracy and time for each chapter
        for chap in range(1, self.num_chap + 1):
            accu_chaps[chap] = sum(accu_chaps[chap]) / len(accu_chaps[chap]) if accu_chaps[chap] else 0
            time_chaps[chap] = sum(time_chaps[chap]) / len(time_chaps[chap]) if time_chaps[chap] else 0

        return accu_chaps, time_chaps # average accuracy per chap, average time per chap
    
    def difficult_percentile_per_chap(self):
        _, diff_ids, diff_nums = self.cal_accu_diff()
        chap_difficulty_count = {chap: {1: 0, 2: 0, 3: 0, 4:0} for chap in range(1, self.num_chap + 1)}
        chap_difficulty_percentile = {chap: {1: 0, 2: 0, 3: 0, 4:0} for chap in range(1, self.num_chap + 1)}
        
        for diff, ids in diff_ids.items():
            for id in ids:
                chap = int(id[1:3])
                chap_difficulty_count[chap][diff] += 1
        
        for chap in chap_difficulty_count:
            for diff in chap_difficulty_count[chap]:
                if diff_nums[diff] != 0:
                    chap_difficulty_percentile[chap][diff] = chap_difficulty_count[chap][diff] / diff_nums[diff] * 100 * self.num_chap
        
        return chap_difficulty_percentile # ti le % dung cua moi do kho moi chuong, cac chuong con lai mac dinh la ko co cau dung
    def find_most_wrong_chap(self):
        accu_chaps, _ = self.short_total_analysis()
        if accu_chaps:
            # Find the chapter with the minimum average accuracy
            most_wrong_chap = min(accu_chaps, key=accu_chaps.get)
            return most_wrong_chap
        return None


class DrawChap(DrawChartBase):
    def difficult_percentile_per_chap(self):
        _, diff_ids, diff_nums = self.cal_accu_diff()
        chap_difficulty_count = {self.num_chap: {1: 0, 2: 0, 3: 0, 4:0}}
        chap_difficulty_percentile = {self.num_chap: {1: 0, 2: 0, 3: 0, 4:0}}
        
        for diff, ids in diff_ids.items():
            for id in ids:
                chap = int(id[1:3])
                chap_difficulty_count[chap][diff] += 1
        for chap in chap_difficulty_count:
            for diff in chap_difficulty_count[chap]:
                if diff_nums[diff] != 0:
                    chap_difficulty_percentile[chap][diff] = chap_difficulty_count[chap][diff] / diff_nums[diff] * 100 * self.num_chap
        
        return chap_difficulty_percentile

# draw_total = DrawTotal("T", 3, "total",5, "specific")
# # print(draw_total.cal_accu_diff())
# # print(draw_total.lessons_id_to_review())
# print(draw_total.short_total_analysis())
# print(draw_total.find_most_wrong_chap())  
# print(draw_total.difficult_percentile_per_chap())
# print(draw_total.previous_results())
# # For chapter-specific analysis
# draw_chap = DrawChap("T", None, "chapter",0, "specific")
# print(draw_chap.cal_accu_diff())
# print(draw_chap.difficult_percentile_per_chap())
# print(draw_chap.lessons_id_to_review())
# print(draw_chap.difficult_percentile_per_chap())
# print(draw_chap.previous_results())



