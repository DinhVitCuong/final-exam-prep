from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = "account"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)

    def __repr__(self):
        return '<User %r>' % self.username

class Universities(db.Model):
    __tablename__="univesity"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    major = db.Column(db.String(300), nullable=False)
    budget = db.Column(db.String(300), nullable=False)
    location = db.Column(db.String(2), nullable=False)
    pass_score = db.Column(db.String(100), nullable=False)

class Subject(db.Model):
    __tablename__="subject"

    id=db.Column(db.String, primary_key=True) # format: A = chu cai dau mon học
    rate = db.Column(db.String, nullable=True) # format: - ngăn cách giữa các độ khó, "_" ngăn cách giữa các chương

class QAs(db.Model):
    __tablename__ = "question-answer"

    id = db.Column(db.String(10), primary_key=True)
    difficulty = db.Column(db.Integer, nullable=True) #0: nhan biet, 1: thong hieu, 2: van dung, 3: van dung cao
    image = db.Column(db.String(100), nullable=True)
    question = db.Column(db.String, nullable=True)
    options = db.Column(db.String, nullable=True)
    answer = db.Column(db.Integer, nullable=True)
    explain = db.Column(db.String, nullable=True)

class Progress(db.Model):
    __tablename__ = "user-progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    user_subject_cat = db.Column(db.String(5), nullable=True)
    target_progress = db.Column(db.String(10), nullable=True)
    base_progress = db.Column(db.String(10), nullable=True)
    progress_1 = db.Column(db.String(300), nullable=True)
    progress_2 = db.Column(db.String(300), nullable=True)
    progress_3 = db.Column(db.String(300), nullable=True)
    wrong_answer = db.Column(db.String, nullable=True)


class Test(db.Model):
    __tablename__ = "test-record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    test_type = db.Column(db.Integer, nullable=False) #1 = Total, 0 = Chapter, 3 = practice
    time = db.Column(db.Date,nullable=False) #Thoi gian lam test
    knowledge = db.Column(db.String(100),nullable=False) #Chapter in test
    questions = db.Column(db.String, nullable=True) #ID all question in test, Format: ID1_ID2_ID3_...
    wrong_answer = db.Column(db.String, nullable=True) #ID wrong test, Format: ID1_ID2_ID3_...
    result = db.Column(db.String(300), nullable=True) # 0 = false, 1 = true, Format: 0_1_0_...
    time_result = db.Column(db.String, nullable=True) #Time spent each question, 0 = not do, Format: time1_time2_time3_...
