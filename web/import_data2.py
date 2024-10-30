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
from models import User, Progress, Test, Universities, QAs, Subject, SubjectCategory, LessonInfo, ProblemTypes
from flask import Flask
import json
from app import create_app, db
from models import ProblemTypes

app = create_app()

path = r'D:\Code\Python\projects\BangA\final-exam-prep\web\H_types.json.json'Q

def commit_data_from_json(path):
    # Sử dụng app context để truy cập và tương tác với database
    with app.app_context():
        # Đọc dữ liệu từ file JSON
        with open(path, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)

            for record in knowledge_data:
                chapter_num = record['Chap_id']
                problem_type = record['problem_type']
                id_subject = record['id_subject']

                new_knowledge = ProblemTypes(
                    id_subject = id_subject,
                    chapter_num=chapter_num,
                    problem_types=problem_type
                )

                # Thêm bản ghi vào session
                db.session.add(new_knowledge)

            print("Dữ liệu đã được thêm vào cho các chương học")

        # Commit tất cả thay đổi vào cơ sở dữ liệu
        try:
            db.session.commit()
            print("Tất cả dữ liệu đã được load thành công vào bảng 'problem_types'.")
        except Exception as e:
            db.session.rollback()
            print("Đã xảy ra lỗi khi commit dữ liệu:", e)

commit_data_from_json(path)
