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
from models import User, Progress, Test, Universities, QAs, Subject, SubjectCategory

app = create_app()
with app.app_context():
#QAs

    folder_path = "data_json/"
    file_names = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    # print(file_names)
    difficulty_mapping = {
        "Nhận biết": 0,
        "Thông hiểu": 1,
        "Vận dụng": 2,
        "Vận dụng cao": 3
    }
    for file_name in file_names:
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Insert each record into the table
            for item in data:
                for k, v in item.items():
                    if item[k] != None and not isinstance(item[k], list) and not isinstance(item[k], int):
                        item[k] = item[k].replace("\\\\", '\\')
                    if isinstance(item[k], list):
                        for i in range(len(item[k])):
                            if item[k][i] != None:
                                item[k][i] = item[k][i].replace("\\\\", '\\')
                # Convert list of options to a single string joined by an underscore "_"
                options_list = item.get('options', [])
                if isinstance(options_list, list):
                    options_str = "__".join(options_list)
                    options_str = options_str.replace("'", "")
                else:
                    options_str = options_list  # If it's not a list, keep as is (or handle accordingly)
                
                if not QAs.query.filter_by(id=item.get('id')).first():
                    new_QAs = QAs(
                        id=item.get('id'),
                        difficulty=difficulty_mapping.get(item.get('difficulty'), -1),
                        image=item.get('image_source'),
                        question=item.get('question'),
                        options=options_str, 
                        answer=item.get('answer'),
                        explain=item.get('explain')
                    )
                    db.session.add(new_QAs)
            # Commit the transaction after each file
            db.session.commit()
            print(f"Data from {file_name} have been successfully imported into the SQLite database.")

# #University Major data
#     folder_path = "uni_data/"
#     file_names = [f for f in os.listdir(folder_path) if f.endswith('.json')]
#     # print(file_names)
#     for file_name in file_names:
#         file_path = os.path.join(folder_path, file_name)
#         if os.path.exists(file_path):
#             with open(file_path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
            
#             # Insert each record into the table
#             for item in data:
#                 if not Universities.query.filter_by(id=item.get('id')).first():
#                     new_Uni = Universities(
#                         id=item.get('id'),
#                         name=item.get('tên trường'),
#                         uni_code=item.get('mã trường'),
#                         subject_category=item.get('tổ hợp'),
#                         major_name=item.get('tên ngành'),
#                         major_code=item.get('mã ngành'),
#                         budget=item.get('học phí'),
#                         location=item.get('khu vực'),
#                         pass_score=item.get('điểm chuẩn')
#                     )
#                     db.session.add(new_Uni)
#             # Commit the transaction after each file
#             db.session.commit()
#             print(f"Data from {file_name} have been successfully imported into the SQLite database.")

# #Subject category data
#     folder_path = "subcat_data/"
#     file_names = [f for f in os.listdir(folder_path) if f.endswith('.json')]
#     # print(file_names)
#     for file_name in file_names:
#         file_path = os.path.join(folder_path, file_name)
#         if os.path.exists(file_path):
#             with open(file_path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
            
#             # Insert each record into the table
#             for item in data:
#                 if not SubjectCategory.query.filter_by(id=item.get('id')).first():
#                     new_Uni = SubjectCategory(
#                         id=item.get('id'),
#                         subject1=item.get('sub1'),
#                         subject2=item.get('sub2'),
#                         subject3=item.get('sub3'),
#                     )
#                     db.session.add(new_Uni)
#             # Commit the transaction after each file
#             db.session.commit()
#             print(f"Data from {file_name} have been successfully imported into the SQLite database.")

#     # Close the session
#     print("Data from all JSON files in the folder have been successfully imported into the SQLite database.")