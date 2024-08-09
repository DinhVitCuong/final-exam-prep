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

class Progress(db.Model):
    __tablename__ = "user-progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    user_subject_cat = db.Column(db.String(5), nullable=False)
    target_progress = db.Column(db.String(10), nullable=True)
    base_progress = db.Column(db.String(10), nullable=True)
    progress_1 = db.Column(db.String(300), nullable=True)
    progress_2 = db.Column(db.String(300), nullable=True)
    progress_3 = db.Column(db.String(300), nullable=True)


class Test(db.Model):
    __tablename__ = "test-record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    test_type = db.Column(db.Boolean, nullable=False) #1 = Total, 0 = Chapter
    knowledge = db.Column(db.String(300),nullable=False) #Chapter in test
    questions = db.Column(db.String(1100), nullable=True)
    wrong_answer = db.Column(db.String(1100), nullable=True)
    result = db.Column(db.String(300), nullable=True)