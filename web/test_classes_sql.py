from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import random
import math
from models import Subject, QAs, Test, Progress
from app import db

def parse_rate_string(rate_string):
    # Split the string by underscores to separate each group
    groups = rate_string.split("_")
    # Split each group by hyphens and convert the values to integers
    parsed_rate = [list(map(int, group.split("-"))) for group in groups]
    return parsed_rate

# Query the database and convert the "rate" column
def get_rate_as_list(test_id):
    # Query the Test model to get the rate string for the given 
    test = Subject.query.filter_by(id=test_id).first()
    if test:
        rate_string = test.rate
        return parse_rate_string(rate_string)
    return None

class TestOrigin:
    def __init__(self, monhoc: str, chapter: int):
        self.monhoc = monhoc
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

    def select_questions(self, rate, num_questions, chapter=None):
        # Query the database for questions
        query = db.session.query(QAs)
        if chapter is not None:
            query = query.filter(
                QAs.id.like(f"{self.monhoc}%"),  # Filter by the subject character at the start
                QAs.id.like(f"_{str(chapter).zfill(2)}%")  # Filter by the two-digit chapter number
            )
        selected_questions = query.all()
        # print(selected_questions)
        # Separate questions by difficulty
        th_questions = [q for q in selected_questions if q.difficulty == 0]
        nb_questions = [q for q in selected_questions if q.difficulty == 1]
        vd_questions = [q for q in selected_questions if q.difficulty == 2]
        vdc_questions = [q for q in selected_questions if q.difficulty == 3]

        # Calculate the number of questions to select for each difficulty level
        th_percent, nb_percent, vd_percent, vdc_percent = rate
        num_th = int(num_questions * th_percent / 100)
        num_nb = int(num_questions * nb_percent / 100)
        num_vd = int(num_questions * vd_percent / 100)
        num_vdc = int(num_questions * vdc_percent / 100)
        
        # Randomly select questions for each difficulty level

        questions = random.choices(th_questions, k=min(num_th, len(th_questions))) + \
            random.choices(nb_questions, k=min(num_nb, len(nb_questions))) + \
            random.choices(vd_questions, k=min(num_vd, len(vd_questions))) + \
            random.choices(vdc_questions, k=min(num_vdc, len(vdc_questions)))
        
        return questions
    def shuffle_questions(self, questions):
        th_questions = [q for q in questions if q.difficulty == 0]
        nb_questions = [q for q in questions if q.difficulty == 1]
        vd_questions = [q for q in questions if q.difficulty == 2]
        vdc_questions = [q for q in questions if q.difficulty == 3]
        
        random.shuffle(th_questions)
        random.shuffle(vd_questions)
        
        random.shuffle(vdc_questions)
        
        return th_questions + nb_questions + vd_questions + vdc_questions

class TestTotal(TestOrigin):
    def create_test(self, rate):
        questions = []
        for i in range(1, self.chapter + 1):
            chapter_questions = self.select_questions(rate, 10, chapter=i)
            questions.extend(chapter_questions)
        questions = self.shuffle_questions(questions)
        self.num_ques = len(questions)
        return questions

    def get_num_questions(self):
        return super().get_num_questions()


class TestChap(TestOrigin):
    def create_test(self,rate):
        questions = self.select_questions(rate, 30, self.chapter)
        self.num_ques = len(questions)
        return questions


class pr_br_rcmd:
    def __init__(self, subject_name, n_total=1, n_chap = 1):
        self.subject_name = subject_name
        self.n_total = n_total # so bai test tong
        self.n_chap = n_chap # so bai test chuong 
        self.top_t = []
        self.top_c = []
        self.chap_freq = {}
        self.aim = 9
        self.load_data()

    def load_data(self):
        try:
            # Load total test results
            total_results = db.session.query(Test).filter_by(test_type=1).order_by(Test.id.desc()).limit(self.n_total).all()
            total_q = []
            count_t = {}

            if total_results:
                for result in total_results:
                    wrong_answers = result.wrong_answer.split('_') if result.wrong_answer else []
                    unchecked_answers = [
                        result.questions.split('_')[i]
                        for i, time in enumerate(result.time_result.split('_'))
                        if time == '0'
                    ] if result.time_result else []
                    
                    for answer in wrong_answers + unchecked_answers:
                        if answer[-1] != '4':  # Filter out certain answers
                            total_q.append(answer)

                for answer in total_q:
                    key = (answer[:5], answer[-1])
                    chapter = answer[1:3]

                    count_t[key] = count_t.get(key, 0) + 1
                    self.chap_freq[chapter] = self.chap_freq.get(chapter, 0) + 1

            self.top_t = sorted(count_t.items(), key=lambda x: x[1], reverse=True)[:5]
            total_sum_all = sum(value for key, value in self.top_t)
            self.top_t = [(key, math.ceil((value / total_sum_all) * 15)) for key, value in self.top_t]

            # Load chapter test results
            chapter_results = db.session.query(Test).filter_by(test_type=0).order_by(Test.id.desc()).limit(self.n_chap).all()
            chap_q = []
            count_c = {}

            for result in chapter_results:
                wrong_answers = result.wrong_answer.split('_') if result.wrong_answer else []
                unchecked_answers = []  # Assuming unchecked answers aren't stored directly

                for answer in wrong_answers + unchecked_answers:
                    if answer[-1] != '4':  # Filter out certain answers
                        chap_q.append(answer)

            for answer in chap_q:
                key = (answer[:5], answer[-1])
                chapter = answer[1:3]

                count_c[key] = count_c.get(key, 0) + 1
                self.chap_freq[chapter] = self.chap_freq.get(chapter, 0) + 1

            self.top_c = sorted(count_c.items(), key=lambda x: x[1], reverse=True)[:3]
            chapter_sum_all = sum(value for key, value in self.top_c)
            self.top_c = [(key, math.ceil((value / chapter_sum_all) * 5)) for key, value in self.top_c]

            # Sort chapter frequencies to find the top 2 chapters
            self.chap_freq = sorted(self.chap_freq.items(), key=lambda x: x[1], reverse=True)[:2]
    
        except Exception as e:
            print(f"Error loading data: {str(e)}")
        
    def containter_type(self, id):  # Return a list of questions for each id
        return db.session.query(QAs).filter(QAs.id.like(f'{id[0][0]}%'), QAs.difficulty == id[0][1]).all()

    def find_vdc(self, id_chap):  # Return a list of VDC questions
        return db.session.query(QAs).filter_by(id=id_chap, difficulty=4).all()

    def question_prep(self):  # Return a test with questions
        QAs_list = []

        for (id, _), num_id in self.top_t:
            matching_questions = self.containter_type((id, _))
            if len(matching_questions) >= num_id:
                QAs_list += random.sample(matching_questions, num_id)
            else:
                QAs_list += matching_questions  # Add all if not enough to sample

        for (id, _), num_id in self.top_c:
            matching_questions = self.containter_type((id, _))
            if len(matching_questions) >= num_id:
                QAs_list += random.sample(matching_questions, num_id)
            else:
                QAs_list += matching_questions  # Add all if not enough to sample

        # Adjust based on aim
        if self.aim >= 9.5:
            vdc_chap_1 = self.find_vdc(self.chap_freq[0][0])
            vdc_chap_2 = self.find_vdc(self.chap_freq[1][0])

            # Check if there are enough questions to sample
            if len(vdc_chap_1) >= 2:
                QAs_list += random.sample(vdc_chap_1, 2)
            else:
                QAs_list += vdc_chap_1  # Add all if not enough to sample

            if len(vdc_chap_2) >= 1:
                QAs_list += random.sample(vdc_chap_2, 1)
            else:
                QAs_list += vdc_chap_2  # Add all if not enough to sample

        elif self.aim >= 9:
            vdc_chap_1 = self.find_vdc(self.chap_freq[0][0])
            vdc_chap_2 = self.find_vdc(self.chap_freq[1][0])

            if len(vdc_chap_1) >= 1:
                QAs_list += random.sample(vdc_chap_1, 1)
            else:
                QAs_list += vdc_chap_1  # Add all if not enough to sample

            if len(vdc_chap_2) >= 1:
                QAs_list += random.sample(vdc_chap_2, 1)
            else:
                QAs_list += vdc_chap_2  # Add all if not enough to sample

        elif self.aim >= 8.5:
            vdc_chap_1 = self.find_vdc(self.chap_freq[0][0])

            if len(vdc_chap_1) >= 1:
                QAs_list += random.sample(vdc_chap_1, 1)
            else:
                QAs_list += vdc_chap_1  # Add all if not enough to sample
        
        if not QAs_list:
            print("Warning: You haven't done any test.")

        return QAs_list if QAs_list else []
    
    
from app import create_app, db, login_manager, bcrypt

# # # Example usage:
# rate = [40, 20, 30, 10]
# test_total = TestTotal("T", 3)
# app = create_app()
# with app.app_context():
#     # Your database operations here
#     # For example, querying the Test model
#     questions_total = test_total.create_test(rate)
#     print("Total Test Questions:", questions_total)

# test_chap = TestChap("T", 3)
# questions_chap = test_chap.create_test(rate)
# print("Chapter Test Questions:", questions_chap)
