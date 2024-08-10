import json
import random

class TestOrigin:
    def __init__(self, monhoc: str):
        self.monhoc = monhoc
        self.num_ques = None
        self.timelimit = None
    def create_test(self):
        pass

    def calculate_score_n_save(self):
        pass

    def is_test_total(self):
        pass

    def is_test_chap(self):
        pass
    def select_question(self):
        pass
    def get_num_questions(self):
        return self.num_ques
class TestTotal(TestOrigin):

    def create_test(self, num_chapters):
        questions = []
        if num_chapters <= 2:
            for i in range(1, num_chapters + 1):
                chapter_questions = self.select_questions(15, 60, 30, 10, chapter=i)
                questions.extend(chapter_questions)

            questions = self.shuffle_questions(questions)
        else:
            for i in range(1, num_chapters + 1):
                chapter_questions = self.select_questions(10, 60, 30, 10, chapter=i)
                questions.extend(chapter_questions)

            questions = self.shuffle_questions(questions)
        self.num_ques = len(questions)
        return questions

    def select_questions(self, num_questions, th_percent, vd_percent, vdc_percent, chapter=None):
        with open(f"{self.monhoc}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        
        selected_questions = []
        for question in mock_db:
            if chapter is None or question["ID"][1:3] == str(chapter).zfill(2):
                selected_questions.append(question)
        
        th_questions = [q for q in selected_questions if q["difficulty"] == "TH"]
        vd_questions = [q for q in selected_questions if q["difficulty"] == "VD"]
        vdc_questions = [q for q in selected_questions if q["difficulty"] == "VDC"]
        
        num_th = int(num_questions * th_percent / 100)
        num_vd = int(num_questions * vd_percent / 100)
        num_vdc = int(num_questions * vdc_percent / 100)
        
        questions = random.sample(th_questions, num_th) + random.sample(vd_questions, num_vd) + random.sample(vdc_questions, num_vdc)
        
        return questions

    def shuffle_questions(self, questions):
        th_questions = [q for q in questions if q["difficulty"] == "TH"]
        vd_questions = [q for q in questions if q["difficulty"] == "VD"]
        vdc_questions = [q for q in questions if q["difficulty"] == "VDC"]
        
        random.shuffle(th_questions)
        random.shuffle(vd_questions)
        random.shuffle(vdc_questions)
        
        return th_questions + vd_questions + vdc_questions
    def get_num_questions(self):
        return super().get_num_questions()
class TestChap(TestOrigin):
    def __init__(self, monhoc: str, chapter: int):
        super().__init__(monhoc)
        self.chapter = chapter

    def create_test(self):
        questions = self.select_questions(30, 60, 30, 10)
        questions = self.shuffle_questions(questions)
        self.num_ques = len(questions)
        return questions
    
    def is_theory(self):
        return self.select_questions(30, 80, 15, 5)

    def is_practice(self):
        return self.select_questions(30, 40, 40, 20)

    def select_questions(self, num_questions, th_percent, vd_percent, vdc_percent):
        with open(f"{self.monhoc}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        
        selected_questions = [q for q in mock_db if q["ID"][1:3] == str(self.chapter).zfill(2)]
        
        th_questions = [q for q in selected_questions if q["difficulty"] == "TH"]
        vd_questions = [q for q in selected_questions if q["difficulty"] == "VD"]
        vdc_questions = [q for q in selected_questions if q["difficulty"] == "VDC"]
        
        num_th = int(num_questions * th_percent / 100)
        num_vd = int(num_questions * vd_percent / 100)
        num_vdc = int(num_questions * vdc_percent / 100)
        
        questions = random.sample(th_questions, num_th) + random.sample(vd_questions, num_vd) + random.sample(vdc_questions, num_vdc)
        
        return questions

    def shuffle_questions(self, questions):
        th_questions = [q for q in questions if q["difficulty"] == "TH"]
        vd_questions = [q for q in questions if q["difficulty"] == "VD"]
        vdc_questions = [q for q in questions if q["difficulty"] == "VDC"]
        
        random.shuffle(th_questions)
        random.shuffle(vd_questions)
        random.shuffle(vdc_questions)
        
        return th_questions + vd_questions + vdc_questions

# Example usage
# "T" is the subject code for "Toan"
test_total = TestTotal("T")
questions_total = test_total.create_test(3) # 3 là số chương đã học
print("Total Test Questions:", questions_total)

test_chap = TestChap("T", 3)
questions_chap = test_chap.create_test()
print("Chapter Test Questions:", questions_chap)
