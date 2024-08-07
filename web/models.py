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
class Progress(db.Model):
    __tablename__ = "user-progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_progress = db.Column(db.String, nullable=False)
    base_progress = db.Column(db.String, nullable=False)
    progress_1 = db.Column(db.String, nullable=False)
    progress_2 = db.Column(db.String, nullable=False)
    progress_3 = db.Column(db.String, nullable=False)