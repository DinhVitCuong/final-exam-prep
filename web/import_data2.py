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

# dic = {
#     "T" : r"C:\Users\VIET HOANG - VTS\Desktop\final-exam-prep-main\web\lesson_info\Link_Maths_dict.json",
#     "L" : r"C:\Users\VIET HOANG - VTS\Desktop\final-exam-prep-main\web\lesson_info\Link_Physics_dict.json",
#     "H" : r"C:\Users\VIET HOANG - VTS\Desktop\final-exam-prep-main\web\lesson_info\Link_Chemistry_dict.json"
# }

# with app.app_context():

#     for subject, path in dic.items():
#         with open(path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#             for chapter, lesson_dic in data.items():
#                 for lesson_num, lesson_name in lesson_dic.items():
#                     lesson = LessonInfo(
#                         subject=subject,
#                         chapter_num=str(chapter),
#                         lesson_num='{:02}'.format(int(lesson_num)),
#                         lesson_name=lesson_name
#                     )
#                     db.session.add(lesson)
#         print("Added lessons for subject", subject)
#     db.session.commit()


import json
# from app import db
from models import Knowledge

# Định nghĩa dictionary chứa các môn học và đường dẫn đến file JSON tương ứng
files_dict = {
    "S1": r"D:\Code\Python\projects\BangA\toan.json",  # File JSON cho môn Toán
    "S2": r"D:\Code\Python\projects\BangA\ly.json",  # File JSON cho môn Lý
    "S3": r"D:\Code\Python\projects\BangA\hoa.json"  # File JSON cho môn Hóa
}

# Dùng app context để truy cập và tương tác với database
with app.app_context():

    # Lặp qua từng môn học và đường dẫn file JSON tương ứng
    for subject, file_path in files_dict.items():
        # Mở file JSON và đọc dữ liệu
        with open(file_path, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)

        # Lặp qua từng bản ghi trong file JSON và thêm vào database
        for record in knowledge_data:
            new_knowledge = Knowledge(
                id_subject=record['id_subject'],
                num_chap=record['num_chap'],
                url_chap=record['url_chap'],
                latex_text=record['latex_content']
            )
            
            # Thêm bản ghi vào session
            db.session.add(new_knowledge)

        print(f"Dữ liệu đã được thêm vào cho môn học {subject}")

    # Commit tất cả thay đổi vào cơ sở dữ liệu
    db.session.commit()

print("Tất cả dữ liệu đã được load thành công vào bảng 'knowledge'.")
