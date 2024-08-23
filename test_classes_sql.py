from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import random
import math
from models import Subject, QAs, Test, Progress

#-------------------------------------------------------------
Base = declarative_base()

# Define the Question model
class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    question_id = Column(String, unique=True, nullable=False)
    chapter = Column(Integer, nullable=False)
    difficulty = Column(Integer, nullable=False)
    content = Column(String, nullable=False)

# Define the Result model
class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)  # 'total' or 'chapter'
    wrong_answers = Column(String)  # You can adjust to store lists of IDs
    unchecked_answers = Column(String)

# Set up the database
engine = create_engine('sqlite:///test.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
#-------------------------------------------------------------


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
        query = session.query(Question)
        if chapter is not None:
            query = query.filter_by(chapter=chapter)
        selected_questions = query.all()

        # Separate questions by difficulty
        th_questions = [q for q in selected_questions if q.difficulty == 1]
        nb_questions = [q for q in selected_questions if q.difficulty == 2]
        vd_questions = [q for q in selected_questions if q.difficulty == 3]
        vdc_questions = [q for q in selected_questions if q.difficulty == 4]

        # Calculate the number of questions to select for each difficulty level
        th_percent, nb_percent, vd_percent, vdc_percent = rate
        num_th = int(num_questions * th_percent / 100)
        num_nb = int(num_questions * nb_percent / 100)
        num_vd = int(num_questions * vd_percent / 100)
        num_vdc = int(num_questions * vdc_percent / 100)

        # Randomly select questions for each difficulty level
        questions = random.sample(th_questions, num_th) + \
                    random.sample(nb_questions, num_nb) + \
                    random.sample(vd_questions, num_vd) + \
                    random.sample(vdc_questions, num_vdc)
        
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


class pr_br_rcmd:
    def __init__(self, subject_name, n_total=0, n_chap=[0]):
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
            # Load total test results
            total_results = session.query(Test).filter_by(test_type=1).order_by(Test.id.desc()).limit(self.n_total).all()
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
            chapter_results = session.query(Test).filter_by(test_type=0).order_by(Test.id.desc()).limit(self.n_chap).all()
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
        return session.query(QAs).filter(QAs.id.like(f'{id[0][0]}%'), QAs.difficulty == id[0][1]).all()

    def find_vdc(self, id_chap):  # Return a list of VDC questions
        return session.query(QAs).filter_by(id=id_chap, difficulty=4).all()

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
            QAs_list += random.sample(self.find_vdc(self.chap_freq[0][0]), 2)
            QAs_list += random.sample(self.find_vdc(self.chap_freq[1][0]), 1)
        elif self.aim >=9:
            QAs_list += random.sample(self.find_vdc(self.chap_freq[0][0]), 1)
            QAs_list += random.sample(self.find_vdc(self.chap_freq[1][0]), 1)
        elif self.aim >= 8.5:
            QAs_list += random.sample(self.find_vdc(self.chap_freq[0][0]), 1)

        return QAs_list


# # Example usage:
# rate = [40, 20, 30, 10]
# test_total = TestTotal("T", rate, 3)
# questions_total = test_total.create_test()
# print("Total Test Questions:", questions_total)

# test_chap = TestChap("T", rate, 3)
# questions_chap = test_chap.create_test()
# print("Chapter Test Questions:", questions_chap)
