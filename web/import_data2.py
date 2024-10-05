from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    request,
    url_for,
    session
)

from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError
import os
import json
from app import create_app, db, login_manager, bcrypt
from models import User, Progress, Test, Universities, QAs, Subject, SubjectCategory, LessonInfo

app = create_app()

dic = {
    "T" : r"C:\Users\VIET HOANG - VTS\Desktop\final-exam-prep-main\web\lesson_info\Link_Maths_dict.json",
    "L" : r"C:\Users\VIET HOANG - VTS\Desktop\final-exam-prep-main\web\lesson_info\Link_Physics_dict.json",
    "H" : r"C:\Users\VIET HOANG - VTS\Desktop\final-exam-prep-main\web\lesson_info\Link_Chemistry_dict.json"
}

with app.app_context():

    for subject, path in dic.items():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for chapter, lesson_dic in data.items():
                for lesson_num, lesson_name in lesson_dic.items():
                    lesson = LessonInfo(
                        subject=subject,
                        chapter_num=str(chapter),
                        lesson_num='{:02}'.format(int(lesson_num)),
                        lesson_name=lesson_name
                    )
                    db.session.add(lesson)
        print("Added lessons for subject", subject)
    db.session.commit()

# a = '{:02}'.format('3')
# print(a)