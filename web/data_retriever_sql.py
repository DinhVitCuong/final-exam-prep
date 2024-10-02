import json
import os
import pandas as pd 
from app import create_app, db, login_manager, bcrypt
from models import User, Progress, Test, Universities, QAs, Subject, SubjectCategory
app = create_app()

class DrawChartBase:
    def __init__(self, subject_name, num_chap, test_type, num, load_type = None, ) -> None:
        self.subject_name = subject_name
        self.num_chap = num_chap
        self.test_type = test_type # 1 : total, 0: chapter, 3: practice
        self.num = num
        self.load_type = load_type if load_type in ["specific", "average"] else None # picking specefic to load specific test from the database
        self.time_to_do_test = None
        self.data = None
        self.date_and_time_calc("2024-08-23", "2025-06-27", 9)
        self.rate = [40,20,30,10]
    def load_data(self):
        try:
            self.data = db.session.query(Test).filter(
                Test.questions.like(f"{self.subject_name}%")
            )
            if self.load_type == None or self.load_type == "average":
                if self.test_type == 1: 
                    self.data = db.session.query(Test).filter_by(
                        test_type = self.test_type,
                    ).order_by(Test.id.desc()).limit(self.num).all()
                    print("hi")
                    self.num_chap = max([int(test.knowledge) for test in self.data])
                    
                elif self.test_type == 0:
                    self.data = db.session.query(Test).filter_by(
                        test_type = self.test_type,
                        knowledge = str(self.num_chap).zfill(2)
                    ).order_by(Test.id.desc()).limit(self.num).all()
                    
            else:
                query = db.session.query(Test).filter_by(
                    test_type = self.test_type
                ).all()
                self.data = [query[self.num]]
                self.num_chap = int(self.data[0].knowledge)

        except FileNotFoundError:
            print(f"Error: cai gi do roi")
            return None

    def cal_accu_diff(self): # accuracy per diff (để vẽ accuracy giữa các độ khó), list right ID per diff , total number of question per diff
        dic_right = {}
        dic_total = {}
        dic_ques = {}
        datas = self.data
        for data in datas:
            
            mock_test = data.questions.split("_")
            right_answers = [id for num, id in enumerate(data.questions.split('_')) if data.result.split('_')[num] == '1']
            if data is not None:
                for id in right_answers:
                    matching_question = db.session.query(QAs).filter_by(id = id).first() # tim cau hoi trong database, ko can load het ra
                    if matching_question:
                        diff = matching_question.difficulty
                        if diff in dic_right:
                            dic_right[diff] += 1
                        else:
                            dic_right[diff] = 1
                        if diff in dic_ques:
                            dic_ques[diff].append(id)
                        else:
                            dic_ques[diff] = [id]
            
            for id in mock_test:
                diff = db.session.query(QAs).filter_by(id = id).first().difficulty
                if diff in dic_total:
                    dic_total[diff] += 1
                else:
                    dic_total[diff] = 1

        accu_diff = {}
        for diff in dic_total:
            accu_diff[diff] = dic_right.get(diff, 0) / dic_total[diff] * 100
        
        for i in range(0,4):
            if i not in dic_total:
                dic_total[i] = 0
            if i not in accu_diff:
                accu_diff[i] = 0
        return accu_diff, dic_ques, dic_total # accuracy per diff (để vẽ accuracy giữa các độ khó), list right ID per diff , total number of question per diff
    def lessons_id_to_review(self): # trả về số lần sai trung bình của các bài học sau self.num lần thi
        datas = self.data
        lessons_review_dict = {}
        for data in datas:
            if data is not None:
                for id in data.wrong_answer.split('_'):
                    chap = id[1:3]
                    lesson = id[3:5]
                    id_l = id[5:]
                    
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

        # R0 : bài ôn tập
        return lessons_review_dict

    def previous_results(self): # trả về list result, list tổng duration, list thời gian thi, list số câu hỏi
        results = []
        durations = []
        exact_time = []
        num_quess = []
        datas = self.data
        for a in datas:
            num_ques = len(a.questions.split("_"))
            num_quess.append(num_ques)
            duration = 0
            score = len([id for id in a.result.split('_') if id == '1']) / num_ques 
            results.append(score*10)
            for time in a.time_result.split('_'):
                duration += float(time)
            durations.append(duration)
            exact_time.append(a.time)
        return results, durations, exact_time,  num_quess # list of scores, list of durations, list of exact time
    
    def date_and_time_calc(self,start_date, final_date, aim): # tìm ra khoảng cách thời gian giữa các lần thi (total, chapter)
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
        if self.test_type == 1:
            self.time_to_do_test = (get_date_prep - start_date)/7
        elif self.test_type == 0:
            self.time_to_do_test = (get_date_prep - start_date)/14
        return get_date_prep
    
    def return_max_chap(self):
        return self.num_chap

class DrawTotal(DrawChartBase):
    def __init__(self, subject_name, num_chap, test_type, num, load_type=None) -> None:
        super().__init__(subject_name, num_chap, test_type, num, load_type)
        self.test_type = 1
        self.load_data()
    def cal_accu_chap(self, chap): # accuracy từng chapter
        datas = self.data
        scores = []
        for data in datas:
            score = 0
            right_answers = [id for num, id in enumerate(data.questions.split('_')) if data.result.split('_')[num] == '1']
            if data is not None:
                for id in right_answers:
                    if id[1:3] == str(chap).zfill(2):
                        score += 1
                if self.num_chap <= 2:
                    num_ques = 10 # fix later
                else:
                    num_ques = 10
            scores.append(score / num_ques * 100)
        return sum(scores) / self.num
    
    def cal_time_chap(self, chap): # thời gian làm bài từng chap
        datas = self.data
        times = []
        for data in datas:
            time = 0
            if data is not None:
                time_list = data.time_result.split('_')
                for i in range(len(time_list)):
                    if data.questions.split('_')[i][1:3] == str(chap).zfill(2):
                        time += float(time_list[i])
            times.append(time)
        return sum(times) / self.num
    
    
    def short_total_analysis(self): # trả về accuracy và thời gian làm bài trung bình từng chương
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
    
    def difficult_percentile_per_chap(self): # trả về ti le % dung cua moi do kho moi chuong, cac chuong con lai mac dinh la ko co cau dung
        # tìm ra số loại câu hỏi của của từng chương, tìm số câu đúng của mỗi loại câu hỏi của từng chương, sau đó tính accuracy
        
        _, diff_ids, _ = self.cal_accu_diff()
        chap_difficulty_count = {chap: {0: 0, 1: 0, 2: 0, 3:0} for chap in range(1, self.num_chap + 1)}
        chap_difficulty_percentile = {chap: {0: 0, 1: 0, 2: 0, 3:0} for chap in range(1, self.num_chap + 1)}
        
        for diff, ids in diff_ids.items():
            for id in ids:
                chap = int(id[1:3])
                chap_difficulty_count[chap][diff] += 1

        diff_nums = {0: 0, 1: 0, 2: 0, 3: 0}
        for rate in self.rate:
            diff_nums[self.rate.index(rate)] = rate / 100 * 10 * self.num

        for chap in chap_difficulty_count:
            for diff in chap_difficulty_count[chap]:
                if diff_nums[diff] != 0:
                    chap_difficulty_percentile[chap][diff] = chap_difficulty_count[chap][diff] / diff_nums[diff] * 100 # so loai cau trong chap do
        
        return chap_difficulty_percentile 
    
    def find_most_wrong_chap(self): # Tìm chương sai nhiều nhất (trả về 1 list nếu nhiều hơn 1 chương)
        accu_chaps, _ = self.short_total_analysis()
        if accu_chaps:
            # Find the chapter with the minimum average accuracy
            res = []
            most_wrong_chap = min(accu_chaps, key=accu_chaps.get)
            for i in accu_chaps:
                if accu_chaps[i] == accu_chaps[most_wrong_chap]:
                    res.append(i)
            return res
        return None

        
class DrawChap(DrawChartBase):
    def __init__(self, subject_name, num_chap, test_type, num, load_type=None) -> None:
        super().__init__(subject_name, num_chap, test_type, num, load_type)
        self.test_type = 0
        self.load_data()
    def difficult_percentile_per_chap(self): # trả về tỉ lệ % các độ khó trong chương
        _, diff_ids, diff_nums = self.cal_accu_diff()
        chap_difficulty_count = {self.num_chap: {0: 0, 1: 0, 2: 0, 3:0}}
        chap_difficulty_percentile = {self.num_chap: {0: 0, 1: 0, 2: 0, 3:0}}
        

        for diff, ids in diff_ids.items():
            for id in ids:
                chap = int(id[1:3])
                chap_difficulty_count[chap][diff] += 1
        diff_nums = {0: 0, 1: 0, 2: 0, 3: 0}
        for rate in self.rate:
            diff_nums[self.rate.index(rate)] = rate / 100 * 10 * self.num
        
        for chap in chap_difficulty_count:
            for diff in chap_difficulty_count[chap]:
                if diff_nums[diff] != 0:
                    chap_difficulty_percentile[chap][diff] = chap_difficulty_count[chap][diff] / diff_nums[diff] * 100
        
        return chap_difficulty_percentile
    


# with app.app_context():     #chap  #test_type    #self.num
#     # test = DrawTotal("L", None , None, 10, "average")
#     # print(test.difficult_percentile_per_chap())
#     # # print(test.data)
#     # print(test.cal_accu_diff())
#     # #print(test.lessons_id_to_review())
#     # print(test.previous_results())
#     # # print(test.short_total_analysis())
    
#     # # print(test.find_most_wrong_chap())
#     test = DrawChap("L", 3 , None, 3, "average")
#     # print(test.cal_accu_diff())
#     print(test.difficult_percentile_per_chap())
    
