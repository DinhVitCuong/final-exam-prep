from app import db
from flask_login import UserMixin
import datetime
class User(UserMixin, db.Model):
    __tablename__ = "account"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)
    uni_select = db.Column(db.Integer,nullable=False) #0 = not select uni yet, 1 = selected uni
    def __repr__(self):
        return '<User %r>' % self.username

class Universities(db.Model):
    __tablename__="university"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    uni_code = db.Column(db.String, nullable=False)
    subject_category = db.Column(db.String, nullable=False)
    major_name = db.Column(db.String, nullable=False)
    major_code = db.Column(db.String,nullable=False)
    budget = db.Column(db.String, nullable=False)
    location = db.Column(db.String(2), nullable=False)
    pass_score = db.Column(db.String, nullable=False)

class Subject(db.Model):
    __tablename__="subject"

    id=db.Column(db.String, primary_key=True) # format: A = chu cai dau mon học
    rate = db.Column(db.String, nullable=True) # format: "_" ngăn cách giữa các độ khó, ";" ngăn cách giữa các chương

class QAs(db.Model):
    __tablename__ = "question-answer"

    id = db.Column(db.String(10), primary_key=True)
    difficulty = db.Column(db.Integer, nullable=True) #0: nhan biet, 1: thong hieu, 2: van dung, 3: van dung cao
    image = db.Column(db.String, nullable=True)
    question = db.Column(db.String, nullable=True)
    options = db.Column(db.String, nullable=True)
    answer = db.Column(db.Integer, nullable=True)
    explain = db.Column(db.String, nullable=True)

class Progress(db.Model):
    __tablename__ = "user-progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    user_subject_cat = db.Column(db.String, nullable=True) #example: A00 ??
    user_major_uni = db.Column(db.Integer, db.ForeignKey('university.id'), nullable=False)
    target_progress = db.Column(db.String, nullable=True) #format: subject1_subject2_subject3
    base_progress = db.Column(db.String, nullable=True) #format: subject1_subject2_subject3
    progress_1 = db.Column(db.String, nullable=True) #format: "_" ngăn cách giữa các độ khó, ";" ngăn cách giữa các chương. example: 1_2_3_4;3_1_6_4;...
    threadhold_1 = db.Column(db.String, nullable=True) #format: thread1_thread2_thread3_...
    progress_2 = db.Column(db.String, nullable=True)
    threadhold_2 = db.Column(db.String, nullable=True)
    progress_3 = db.Column(db.String, nullable=True)
    threadhold_3     = db.Column(db.String, nullable=True)
    wrong_answer = db.Column(db.String, nullable=True)
# table phan tich
# id, user_id, subject_id, date, analysis

class Test(db.Model):
    __tablename__ = "test-record" 
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    test_type = db.Column(db.Integer, nullable=False) #1 = Total, 0 = Chapter, 3 = practice
    time = db.Column(db.Date,nullable=False) #Thoi gian lam test
    knowledge = db.Column(db.String(100),nullable=False) #Chapter in test
    questions = db.Column(db.String, nullable=True) #ID all question in test, Format: ID1_ID2_ID3_... # H0101001 - ten mon - so chuong - so bai - id
    wrong_answer = db.Column(db.String, nullable=True) #ID wrong test, Format: ID1_ID2_ID3_...
    result = db.Column(db.String(300), nullable=True) # 0 = false, 1 = true, Format: 0_1_0_...
    time_result = db.Column(db.String, nullable=True) #Time spent each question, 0 = not do, Format: time1_time2_time3_...


class TodoList(db.Model):
    __tablename__ = "todo_list"

    todo_id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), primary_key=True, nullable=False)
    date = db.Column(db.String, nullable=False)  # 12/4/2021
    action = db.Column(db.String, nullable=False)  # do 1
    status = db.Column(db.String, nullable=False)  # 1: done, 0 = not done

class SubjectCategory(db.Model):
    __tablename__="subject-category"

    id = db.Column(db.String, primary_key=True)
    subject1 = db.Column(db.String, nullable=False)
    subject2 = db.Column(db.String, nullable=False)
    subject3 = db.Column(db.String, nullable=False)

class Analysis(db.Model):
    __tablename__ = "analysis"

    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), primary_key=True, nullable=False)
    analysis_type = db.Column(db.String,primary_key=True, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'),primary_key=True, nullable=False)
    num_chap = db.Column(db.Integer,primary_key=True, nullable=False)
    main_text = db.Column(db.Text, nullable=False)


class Knowledge(db.Model):
    __tablename__ = "knowledge"

    id_subject = db.Column(db.Integer, db.ForeignKey('subject.id'), primary_key=True, nullable=False)
    num_chap = db.Column(db.Integer, primary_key=True, nullable=False)
    url_chap = db.Column(db.String, nullable=False)
    latex_text = db.Column(db.Text, nullable=False)

class TempTest(db.Model):
    __tablename__ = "temp_test"
    id = db.Column(db.String(36), primary_key=True)  # UUID as primary key
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    subject = db.Column(db.String(10), nullable=False)
    questions = db.Column(db.PickleType, nullable=False)  # Store as a pickled object
    chapter = db.Column(db.Integer, nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.PickleType, nullable=False)


class TestDate(db.Model):
    __tablename__ = "test_date"
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), primary_key=True, nullable=False)
    test_type = db.Column(db.Integer, primary_key=True, nullable=False)  # 1 = Total, 0 = Chapter, 3 = Practice
    subject = db.Column(db.String(100), primary_key=True, nullable=False)  # Thêm cột subject
    date = db.Column(db.Date, nullable=False)