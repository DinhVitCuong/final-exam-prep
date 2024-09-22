import json
import random

class TestOrigin:
    def __init__(self, monhoc: str, rate : list,chapter: int):
        self.monhoc = monhoc
        self.rate = rate
        self.num_ques = None
        self.timelimit = None   
        self.chapter = chapter
    def create_test(self):
        pass

    def is_test_total(self):
        pass

    def is_test_chap(self):
        pass
    def get_num_questions(self):
        return self.num_ques
    def select_questions(self, num_questions, chapter=None):
        with open(f"{self.monhoc}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        
        selected_questions = []
        for question in mock_db:
            if chapter is None or question["ID"][1:3] == str(chapter).zfill(2):
                selected_questions.append(question)
            
        th_percent, nb_percent, vd_percent, vdc_percent = self.rate

        th_questions = [q for q in selected_questions if q["difficulty"] == 1]
        nb_questions = [q for q in selected_questions if q["difficulty"] == 2]
        vd_questions = [q for q in selected_questions if q["difficulty"] == 3]
        vdc_questions = [q for q in selected_questions if q["difficulty"] == 4]
        
        num_th = int(num_questions * th_percent / 100)
        num_nb = int(num_questions * nb_percent / 100)
        num_vd = int(num_questions * vd_percent / 100)
        num_vdc = int(num_questions * vdc_percent / 100)
        
        questions = random.sample(th_questions, num_th) + random.sample(nb_questions, num_nb) + random.sample(vd_questions, num_vd) + random.sample(vdc_questions, num_vdc)
        
        return questions
    

    
class TestTotal(TestOrigin):

    def create_test(self):
        questions = []
        if self.chapter <= 2:
            for i in range(1, self.chapter + 1):
                chapter_questions = self.select_questions(15, chapter=i)
                questions.extend(chapter_questions)

        
        else:
            for i in range(1, self.chapter + 1):
                chapter_questions = self.select_questions(10, chapter=i)
                questions.extend(chapter_questions)
        self.num_ques = len(questions)
        return questions

    
    def get_num_questions(self):
        return super().get_num_questions()
    
class TestChap(TestOrigin):

    def create_test(self):
        questions = self.select_questions(30, self.chapter)
        self.num_ques = len(questions)
        return questions
    
    def is_theory(self):
        return self.select_questions(30, 80, 15, 5)

    def is_practice(self):
        return self.select_questions(30, 40, 40, 20)

    

# Example usage
# "T" is the subject code for "Toan"
rate = [40,20,30,10]
# test_total = TestTotal("T",rate, 3)
# questions_total = test_total.create_test() # 3 là số chương đã học
# print("Total Test Questions:", questions_total)

test_chap = TestChap("T", rate, 3)
questions_chap = test_chap.create_test()
print("Chapter Test Questions:", questions_chap)
