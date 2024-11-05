from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    request,
    url_for,
    session, 
    jsonify
)

import subprocess
import redis
import threading
import re
from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)
import json
from app import create_app, db, login_manager, bcrypt
from models import User, Progress, Test, Universities, QAs, Subject, TodoList, SubjectCategory, TempTest, Analysis, TestDate, Knowledge, Threshold
from forms import login_form,register_form, test_selection_form, select_univesity_form,QuizForm
from test_classes_sql import TestChap, TestTotal, pr_br_rcmd
from gpt_integrate_sql import promptCreation,promptTotal,promptChap,generateAnalysis
from data_retriever_sql import DrawChartBase
from datetime import datetime
from collections import Counter
import time
from uuid import uuid4

# app = create_app()
# with app.app_context():     #chap  #test_type    #self.num
#     num_test = 5
#     subject = 'L'
#     user_id = 34
#     progressChap = 7
#     data_retrieve = promptTotal(1, num_test, subject, user_id, progressChap , is_final = True)
#     acuc_chaps, time_chaps = data_retrieve.data.short_total_analysis() # percent-chap (% dung tung chuong)
#     accu_diff, dic_ques, dic_total = data_retrieve.data.cal_accu_diff() # button-diff (nếu select = Tất cả) (% dung tung loai cau hoi )
#     chap_difficulty_percentile = data_retrieve.data.difficult_percentile_per_chap() # button-diff (nếu select chọn từ 1- 7) (% dung tung loai cau hoi tung chuong)
#     results, durations, exact_time, nums = data_retrieve.data.previous_results() # button-prev (kết quả các bài test trước)
#     print(acuc_chaps, time_chaps, accu_diff, dic_ques, dic_total, chap_difficulty_percentile, results, durations, exact_time, nums)