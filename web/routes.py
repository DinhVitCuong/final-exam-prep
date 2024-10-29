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
from models import User, Progress, Test, Universities, QAs, Subject, TodoList, SubjectCategory, TempTest, Analysis, TestDate, Knowledge
from forms import login_form,register_form, test_selection_form, select_univesity_form,QuizForm
from test_classes_sql import TestChap, TestTotal, pr_br_rcmd
from gpt_integrate_sql import promptCreation,promptTotal,promptChap,generateAnalysis
from data_retriever_sql import DrawChartBase
from datetime import datetime
from collections import Counter
import time
from uuid import uuid4

########################### DEF FUNCTION #######################

def get_test_count_dates(current_user_id):
    dates = Test.query.filter(
    Test.user_id == current_user_id
    ).with_entities(Test.time).order_by(Test.time.desc()).all()

    # Convert the result to a list of date strings in "YYYY-MM-DD" format
    date_list = [date.time.strftime("%Y-%m-%d") for date in dates]
    date_list
    date_counts = Counter(date_list)

    # Convert to list of dictionaries with 'date' and 'count' keys
    data = [{"date": date, "count": count} for date, count in date_counts.items()]
    return data


def get_max_chapter(subject):
    max_chapter_record = QAs.query.filter(
        QAs.id.like(f'{subject}%')
    ).order_by(QAs.id.desc()).first()

    max_chapter = 1
    if max_chapter_record:
        # Extract the 2-digit chapter number from the ID
        match = re.search(rf'{subject}(\d{{2}})', max_chapter_record.id)
        if match:
            max_chapter = int(match.group(1))
    return max_chapter

def get_mean_grade(current_user_id, subject):
    # Fetch the last 10 records that match the criteria
    records = Test.query.filter(
        Test.user_id == current_user_id,
        Test.test_type == 1,
        Test.questions.like(f'{subject}%')
    ).order_by(Test.time.desc()).limit(10).all()
    
    # Initialize variables for total grade calculation and tracking chapters
    total_grade = 0
    num_records = len(records)
    max_chap = 1
    grade_list = []
    for record in records:
        # Split the result string and count the number of '1's
        results = record.result.split('_')
        num_ones = results.count('1')
        question_count = len(results)
        
        # Scale the number of '1's to a grade out of 10 (as a percentage)
        grade = (num_ones / question_count) * 10
        # Add the grade to the total grade sum
        total_grade += grade
        grade_list.append(round(grade, 2))
        
        # Update the maximum chapter if necessary
        tempChap = int(record.knowledge)
        if tempChap >= max_chap:
            max_chap = tempChap
    
    # Calculate the mean grade
    mean_grade = total_grade / num_records if num_records > 0 else 0
    return round(mean_grade, 2), max_chap, grade_list

def get_chapter_mean_list(current_user_id, subject):
    # Fetch all records that match the criteria
    records = Test.query.filter(
        Test.user_id == current_user_id,
        Test.test_type == 0,
        Test.questions.like(f'{subject}%')
    ).all()
    
    max_chapter = get_max_chapter(subject)
    print(f"Max chapter: {max_chapter}")
    
    # Dictionaries to hold the total grade and count per chapter (knowledge value)
    knowledge_total_grades = {}
    knowledge_counts = {}

    for record in records:
        # Split the result string to count the number of 1s
        num_ones = record.result.split('_').count('1')
        
        # Calculate the total number of questions
        question_count = len(record.result.split('_'))
        
        # Scale the grade to a score out of 10
        grade = (num_ones / question_count) * 10

        # Track the total grade and count for each knowledge (chapter) value
        knowledge = int(record.knowledge)
        if knowledge in knowledge_total_grades:
            knowledge_total_grades[knowledge] += grade
            knowledge_counts[knowledge] += 1
        else:
            knowledge_total_grades[knowledge] = grade
            knowledge_counts[knowledge] = 1

    # Create the mean grade list per chapter
    chapter_mean_list = [0] * max_chapter

    for knowledge, total_grade in knowledge_total_grades.items():
        # Calculate the mean grade for each chapter and place it in the list
        if 1 <= knowledge <= max_chapter:
            mean_grade = total_grade / knowledge_counts[knowledge]
            chapter_mean_list[knowledge - 1] = round(mean_grade, 2)
    
    return chapter_mean_list

def get_chapter_best_list(current_user_id, subject):
    records = Test.query.filter(
        Test.user_id == current_user_id,
        Test.test_type == 0,
        Test.questions.like(f'{subject}%')
    ).all()
    max_chapter = get_max_chapter(subject)
    print(f"max chapter:{max_chapter}")
    knowledge_best_grades = {}

    for record in records:
        # Split the result string to count the number of 1s
        num_ones = record.result.split('_').count('1')
        
        # Calculate the total number of questions
        question_count = len(record.result.split('_'))
        
        # Scale the grade to a score out of 10
        grade = (num_ones / question_count) * 10

        # Update the best grade for each knowledge value
        knowledge = record.knowledge
        if knowledge not in knowledge_best_grades or knowledge_best_grades[knowledge] < grade:
            knowledge_best_grades[knowledge] = grade

    # Build the list where index represents the chapter number minus one
    chapter_best_list = [0] * max_chapter

    for knowledge, grade in knowledge_best_grades.items():
        if int(knowledge) <= int(max_chapter):
            chapter_best_list[int(knowledge) - 1] = int(round(grade))
    
    return chapter_best_list

########################### BEGIN ROUND ########################

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)

@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    else:
        return redirect(url_for('home'))
    # user_id = current_user.id 
    # user_progress = Progress.query.filter_by(user_id=user_id).first()
    # print(user_progress)
    # return render_template("index.html",title="Home", user_progress = user_progress)


# Login route
@app.route("/login", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter(
                (User.email == form.identifier.data) | (User.username == form.identifier.data)
            ).first()
            if check_password_hash(user.pwd, form.pwd.data):
                remember = form.remember.data
                login_user(user, remember=remember, duration=timedelta(days=30))
                return redirect(url_for('index'))
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )

# Register route
@app.route("/register", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit(): 
        try:
            name=form.name.data
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data
            print(email,pwd,username,name)
            newuser = User(
                name=name,
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
                uni_select=0
            )
    
            db.session.add(newuser)
            db.session.commit()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account"
        )



# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/settings")
def settings():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    return render_template('settings.html', title="Cài đặt")


#Home route
@app.route("/home", methods=("GET", "POST"), strict_slashes=False)
def home():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    progress = Progress.query.filter(Progress.user_id==current_user.id).first()
    university = Universities.query.filter(Universities.id==progress.user_major_uni).first()
    subject = SubjectCategory.query.filter(SubjectCategory.id==progress.user_subject_cat).first()

    todo_list = TodoList.query.filter(TodoList.user_id == current_user.id).all()
    todo_l = []
    for todo in todo_list:
        date_string = todo.date 
        todo_date = datetime.strptime(date_string, "%d/%m/%Y").date()
        current_date = datetime.now().date()
        if todo_date == current_date:
            todo_l.append(todo)
    grade_percents = []
    grade_1, max_chap_1, grade_list_1 = get_mean_grade(current_user.id, "T")
    grade_2, max_chap_2, grade_list_2 = get_mean_grade(current_user.id, "L")
    grade_3, max_chap_3, grade_list_3 = get_mean_grade(current_user.id, "H")
    print(f"T: {max_chap_1}, {grade_list_1}")
    print(f"L: {max_chap_2}, {grade_list_2}")
    print(f"H: {max_chap_3}, {grade_list_3}")
    grade_1 = (grade_1/10)/7*max_chap_1*100
    grade_percents.append(grade_1)
    grade_2 = (grade_2/10)/7*max_chap_2*100
    grade_percents.append(grade_2)
    grade_3 = (grade_3/10)/8*max_chap_3*100
    grade_percents.append(grade_3)
    mean_percent = sum(grade_percents) / len(grade_percents)
    grade_percents.append(mean_percent)
    print(grade_percents)

    heat_map_data = get_test_count_dates(current_user.id)
    return render_template("home_new.html", title="Trang chủ", university=university, subject=subject, todo_l = todo_l, grades = grade_percents, grade_list_1 = grade_list_1, grade_list_2 = grade_list_2, grade_list_3 = grade_list_3, heat_map_data = heat_map_data )



@app.route("/select-uni", methods=["GET", "POST"])
def select_uni():
    form = select_univesity_form()
    print("hi ",form.current_slide.data)
    permanace_uni = None
    if int(form.current_slide.data) > 0:
        uni_name = ""
        current_slide = int(form.current_slide.data)
        try:
            budget = int(form.budget.data)
        except:
            budget = 0
        selected_locations = form.location.data
        selected_majors = form.major.data
        selected_subject_category = form.subject_category.data
        query = Universities.query
        majors_score = 0
        print(f"current slide: {current_slide}, budget: {budget}, location: {selected_locations}, major: {selected_majors}, subject_category: {selected_subject_category}")
        
        # Filter by subject category
        query = query.filter(Universities.subject_category.like(f"%{selected_subject_category}%"))
        major_names = query.with_entities(Universities.major_name).distinct().all()
        unique_sorted_majors = sorted({u.major_name for u in major_names})
        form.major.choices = [(major, major) for major in unique_sorted_majors]
        # Filter by majors
        if current_slide>=1:
            query = query.filter(Universities.major_name ==selected_majors)
        # Collect available universities based on selections
        if current_slide>=2:
            #Filter by location
            if selected_locations != 'None':
                query = query.filter(Universities.location == selected_locations)
            # Filter by budget range
            if budget > 0:
                query = query.filter(Universities.budget.isnot(None))  # Ignore universities without a budget
                universities = query.all()
                filtered_universities = []

                for uni in universities:
                    try:
                        budget_range = uni.budget.split('~')
                        if len(budget_range) == 2:
                            lower_budget = int(budget_range[0].replace('tr', '').strip('~'))

                            if budget >= lower_budget:
                                filtered_universities.append(uni)
                    except:
                        # If only a lower limit is provided, check if the budget is higher
                        lower_budget = int(uni.budget.replace('tr', '').strip('~'))
                        if budget >= lower_budget:
                            filtered_universities.append(uni)
                query = query.filter(Universities.id.in_([u.id for u in filtered_universities]))
        universities = query.with_entities(
            Universities.id,
            Universities.name,
            Universities.budget,
            Universities.major_code,
            Universities.uni_code,
            Universities.pass_score
            ).all()
        form.university.choices = [
            (uni.id, f"{uni.name} - {uni.uni_code}\nHọc phí: {uni.budget}\nMã ngành: {uni.major_code}\nĐiểm chuẩn: {uni.pass_score}")
            for uni in universities
            ]
        # form.university.choices = [(u.name, u.name) for u in query.all()]
        # print(form.university.choices)
        selected_university = Universities.query.filter(Universities.id == form.university.data).first()
        if selected_university is not None:
            permanace_uni = selected_university
        print(permanace_uni)
        if current_slide==6:
            return redirect(url_for('home'))
        else: 
            if current_slide==5:
                majors_score = selected_university.pass_score
                uni_name = selected_university.name
                pass_score = float(selected_university.pass_score)
                part_1 = round((pass_score / 3) *4)/4
                part_2 = round((pass_score - 2*part_1 )*4)/4
                target_progress = f"{part_1}_{part_1}_{part_2}"
                try:

                    existing_progress = Progress.query.filter_by(user_id=current_user.id).first()
                    existing_progress.user_major_uni = selected_university.id
                    existing_progress.user_subject_cat = form.subject_category.data
                    existing_progress.target_progress = target_progress
                except:
                    new_progress = Progress(
                        user_id = current_user.id,
                        user_major_uni = selected_university.id,
                        user_subject_cat = form.subject_category.data,
                        target_progress = target_progress
                    )
                    db.session.add(new_progress)
                current_user.uni_select = 1
                db.session.commit()
            return render_template("select_uni.html", form=form, uni_name= uni_name, score= majors_score, current_slide=current_slide)

    # Initialize with an empty list if no submission
    form.major.choices = []
    form.university.choices = []

    return render_template("select_uni.html", form=form,current_slide=0)



import time
@app.route("/total-test/<subject>", methods=["GET"])
def total_test(subject):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    # Determine the chapter based on the subject
    if subject == "T":
        chapter = 7
    elif subject == "L":
        chapter = 7
    else:
        chapter = 8

    time_limit = 90  # Time limit in minutes
    rate = [40, 20, 30, 10]  # Question distribution rates

    # Generate the test questions
    test_total = TestTotal(subject, chapter)
    questions = [{
        "ID": q.id,
        "image": q.image,
        "question": q.question,
        "options": q.options,
        "answer": q.answer,
        "explaination": q.explain
    } for q in test_total.create_test(rate)]

    # Generate a unique test ID
    test_id = str(uuid4())
    user_id = str(current_user.id)
    # Store the test data in the database
    temp_test = TempTest(
        id=test_id,
        user_id=user_id,
        subject=subject,
        questions=questions,
        chapter=chapter,
        time_limit=time_limit,
        rate=rate
    )
    db.session.add(temp_test)
    db.session.commit()
    
    # Pass the test ID to the template
    return render_template('exam.html', subject=subject, time_limit=time_limit, questions=questions, test_id=test_id, chap_id = chapter, user_id = user_id)

@app.route("/total-test/<chap_id>/<subject>", methods=["POST"])
def total_test_post(chap_id, subject):
    # if current_user.is_authenticated == False:
    #     return redirect(url_for('login'))
    # if current_user.uni_select == 0:
    #     return redirect(url_for('select_uni'))
    # Existing logic for processing answers
    
    test_id = request.form.get('test_id')
    user_id = request.form.get('user_id')
    # them user id vao
    temp_test = TempTest.query.filter_by(id=test_id, user_id=user_id).first()

    if not temp_test:
        return "Session expired or invalid test. Please restart the test.", 400

    # Extract the test data
    questions = temp_test.questions
    chapter = temp_test.chapter
    time_spent = request.form.get('timeSpent')
    answers = request.form.get('answers')
    date = datetime.now().date()

    # Convert JSON strings to Python lists
    time_spent = json.loads(time_spent)
    answers = json.loads(answers)

    # Initialize variables for processing
    time_string = ""
    questions_ID_string = ""
    wrong_answer_string = ""
    result = []
    wrong_answers = []

    # Process the answers
    for i, question in enumerate(questions):
        questions_ID_string += f"{question['ID']}_"
        if str(answers[i]) == question["answer"]:
            result.append("1")
        else:
            result.append("0")
            wrong_answers.append(str(question['ID']))
        time_string += f"{time_spent[i]}_"

    # Clean up strings
    questions_ID_string = questions_ID_string.rstrip("_")
    time_string = time_string.rstrip("_")
    wrong_answer_string = "_".join(wrong_answers)
    score = f"{result.count('1')}/{len(result)}"

    # Create a new test record in the database
    new_test_record = Test(
        user_id=user_id,
        test_type=1,  # Total test type
        time=date,
        knowledge=chapter,
        questions=questions_ID_string,
        wrong_answer=wrong_answer_string,
        result="_".join(result),
        time_result=time_string
    )
    db.session.add(new_test_record)
    db.session.commit()

    # Delete the temporary test data
    db.session.delete(temp_test)
    db.session.commit()

    task_id = str(uuid4())

    # Run analysis in a separate thread and pass the app object
    analysis_thread = threading.Thread(target=run_analysis_thread, args=(app, subject, chap_id, user_id, task_id, 1))
    analysis_thread.start()


    # Redirect to the review route
    return render_template("reviewTest.html", questions=questions, wrong_answer_string=wrong_answer_string, score=score, task_id=task_id)
        
@app.route('/subject/<subject_id>', methods=["GET", "POST"])
def subject(subject_id):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    subject_name = ''
    if subject_id == 'S1':  # Toán
        subject_name = 'Toán'
        subject = 'T'
    elif subject_id == 'S2':  # Lí
        subject_name = 'Lí'
        subject = 'L'
    elif subject_id == 'S3':  # Hóa
        subject_name = 'Hóa'
        subject = 'H'
    else:
        return redirect(url_for('home'))

    # Get chapter numbers based on subject_id
    chapter_numbers = (
        QAs.query
        .filter(QAs.id.like(f'{subject}%'))
        .with_entities(db.func.substr(QAs.id, 2, 2).label('chapter_number'))  
        .distinct()
        .all()
    )

    # Convert the results to a list of chapter numbers
    chapter_numbers_list = [f"{int(row.chapter_number):02}" for row in chapter_numbers]    
    grade_subject, max_chap, grade_list_1 = get_mean_grade(current_user.id, subject)
    grade_subject = (grade_subject/10)/7*max_chap*100
    grade_chapters = get_chapter_mean_list(current_user.id,subject)
    grade_chapters = [value * 10 for value in grade_chapters]
    print(grade_subject, grade_chapters)
    # Pass subject_id to the template
    return render_template(
        'subject.html', 
        grade_subject= grade_subject,
        grade_chapters = grade_chapters,
        subject_name=subject_name, 
        subject=subject, 
        chapter_numbers_list=chapter_numbers_list, 
        subject_id=subject_id  # Pass subject_id to the template
    )


# @app.route("/practice-test/<subject>")
# def practice_test(subject):
#     if subject == "T":
#         chapter = 7 
#     elif subject == "L":
#         chapter = 7
#     else:
#         chapter = 8
#     time_limit = 90 #Minute
#     rate = [40, 30, 20, 10]
#     test_prac = pr_br_rcmd(subject, 5, 1)

#     questions = [{"ID": q.id,"image" : q.image, "question": q.question, "options": q.options, "answer": q.answer, "explaination" : q.explain} for q in test_prac.question_prep()]
#     # Kiểm tra nếu phương thức HTTP là POST (khi người dùng gửi câu trả lời)
#     if request.method == "POST":
        
#         time_spent = request.form.get('timeSpent')
#         answers = request.form.get('answers')
#         date= datetime.now().date()
        
#         # Convert từ chuỗi JSON sang danh sách Python
#         time_spent = json.loads(time_spent)
#         answers = json.loads(answers)

#         time_string = ""
#         questions_ID_string = ""
#         wrong_answer_string = ""    
#         chapters = ""
#         result = []  
#         wrong_answers = []

#         # Xử lý dữ liệu câu hỏi
#         for i in range(chapter):
#             chapters += f"{i+1}_"
#         for i, question in enumerate(questions):
#             # Use question["ID"] instead of question.id because the ID is stored as a dictionary key
#             questions_ID_string += f"{question['ID']}_"
#             if str(answers[i]) == question["answer"]:
#                 result.append("1")
#             else:
#                 result.append("0")
#             time_string += f"{time_spent[i]}_"

#             if result[i] == '0':  # Assuming 0 means an incorrect answer
#                 wrong_answers.append(str(question['ID']))

#         # Xóa dấu gạch dưới cuối chuỗi
#         questions_ID_string = questions_ID_string.rstrip("_")
#         time_string = time_string.rstrip("_")   
#         chapter = '{:02}'.format(max(int(chap) for chap in chapters[:-1].split('_') if chap.isdigit()))
#         wrong_answer_string = "_".join(wrong_answers)
        
#         score = f'{result.count("1")}/{len(result)}'
        

#         # Tạo bản ghi mới trong bảng Test
#         new_test_record = Test(
#             user_id=current_user.id,
#             test_type=1,  # Loại bài kiểm tra tổng
#             time=date,
#             knowledge=chapter,
#             questions=questions_ID_string,
#             wrong_answer=wrong_answer_string,
#             result="_".join(result),  # Chuỗi kết quả dạng 0_1_0...
#             time_result=time_string  # Chuỗi thời gian làm từng câu
#         )
#         # nhin vao database sua lai
#         db.session.add(new_test_record)
#         db.session.commit()
        
#         # Sau khi hoàn thành, chuyển hướng về trang chủ
#         return render_template("reviewTest.html", questions=questions, wrong_answer_string=wrong_answer_string, score=score)

    
#     return render_template('exam.html', subject=subject, time_limit = time_limit, questions=questions)



@app.route("/practice-test/<subject>", methods=["GET"])
def practice_test(subject):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    # Xác định chapter theo subject
    if subject == "M":
        chapter_count = 7
    elif subject == "L":
        chapter_count = 7
    else:
        chapter_count = 8

    time_limit = 45  
    rate = [40, 20, 30, 10]     
    user_id = str(current_user.id)
    if request.method == "GET":
        test_prac = pr_br_rcmd(subject, 5, 1)  #  so bai test tong, chuong
    
        # Chuẩn bị câu hỏi sử dụng hàm question_prep của pr_br_rcmd
        questions = [{"ID": q.id, 
                      "image": q.image, 
                      "question": q.question, 
                      "options": q.options, 
                      "answer": q.answer, 
                      "explaination": q.explain} for q in test_prac.question_prep()]


        # Generate a unique test ID
        test_id = str(uuid4())
        user_id = str(current_user.id)
        # Store the test data in the database
        temp_test = TempTest(
            id=test_id,
            user_id=user_id,
            subject=subject,
            questions=questions,
            chapter='05',
            time_limit=time_limit,
            rate=rate
        )
        db.session.add(temp_test)
        db.session.commit()
        
        return render_template('practice_exam.html', subject=subject, time_limit=time_limit, questions=questions, test_id=test_id, user_id = user_id)

        

@app.route("/practice-test/<subject>", methods=["POST"])
def practice_test_post(subject):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    # Extract the test data
    # Retrieve the test ID from the form data
    test_id = request.form.get('test_id')
    user_id = request.form.get('user_id')
    # Retrieve the stored test data using the test ID
    temp_test = TempTest.query.filter_by(id=test_id, user_id=user_id).first()
    if not temp_test:
        return "Session expired or invalid test. Please restart the test.", 400

    questions = temp_test.questions
    chapter = temp_test.chapter
    time_spent = request.form.get('timeSpent')
    answers = request.form.get('answers')
    date = datetime.now().date()

    # Convert JSON strings to Python lists
    time_spent = json.loads(time_spent)
    answers = json.loads(answers)

    # Initialize variables for processing
    time_string = ""
    questions_ID_string = ""
    wrong_answer_string = ""
    result = []
    wrong_answers = []

    # Process the answers
    for i, question in enumerate(questions):
        questions_ID_string += f"{question['ID']}_"
        if str(answers[i]) == question["answer"]:
            result.append("1")
        else:
            result.append("0")
            wrong_answers.append(str(i)) 
        time_string += f"{time_spent[i]}_"

    # Clean up strings
    questions_ID_string = questions_ID_string.rstrip("_")
    time_string = time_string.rstrip("_")
    wrong_answer_string = "_".join(wrong_answers)
    score = f"{result.count('1')}/{len(result)}"

    # Create a new test record in the database
    # new_test_record = Test(
    #     user_id=current_user.id,
    #     test_type=1,  # Total test type
    #     time=date,
    #     knowledge=chapter,
    #     questions=questions_ID_string,
    #     wrong_answer=wrong_answer_string,
    #     result="_".join(result),
    #     time_result=time_string
    # )
    # db.session.add(new_test_record)
    # db.session.commit()

    # Delete the temporary test data
    db.session.delete(temp_test)
    db.session.commit()
    
    task_id = str(uuid4())

    chap_id = 0
    # Run analysis in a separate thread and pass the app object
    analysis_thread = threading.Thread(target=run_analysis_thread, args=(app, subject, chap_id , user_id, task_id, 3))
    analysis_thread.start()
    
    # Redirect to the review route
    return render_template("reviewTest.html", questions=questions, wrong_answer_string=wrong_answer_string, score=score, task_id = task_id)


@app.route("/chapter-test/<chap_id>/<subject>", methods=["GET"])
def chapter_test(chap_id, subject):  # Nhận trực tiếp cả chap_id và subject từ URL
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    time_limit = 45  # Giới hạn thời gian là 45 phút
    rate = [40, 20, 30, 10]  # Tỷ lệ câu hỏi trong bài kiểm tra

    # Generate the test questions
    test_total = TestChap(subject, chap_id)
    questions = [{
        "ID": q.id,
        "image": q.image,
        "question": q.question,
        "options": q.options,
        "answer": q.answer,
        "explaination": q.explain
    } for q in test_total.create_test(rate)]

    # Generate a unique test ID
    test_id = str(uuid4())
    user_id = str(current_user.id)
    # Store the test data in the database
    temp_test = TempTest(
        id=test_id,
        user_id=user_id,
        subject=subject,
        questions=questions,
        chapter=chap_id,
        time_limit=time_limit,
        rate=rate
    )
    db.session.add(temp_test)
    db.session.commit()

    # Pass the test ID to the template
    return render_template('chapter_exam.html', subject=subject, time_limit=time_limit, questions=questions, test_id=test_id, chap_id = chap_id, user_id = user_id, )

        
        
@app.route("/chapter-test/<chap_id>/<subject>", methods=["POST"])
def chapter_test_post(chap_id, subject):
    # if current_user.is_authenticated == False:
    #     return redirect(url_for('login'))
    # if current_user.uni_select == 0:
    #     return redirect(url_for('select_uni'))
    # Existing logic for processing answers

    test_id = request.form.get('test_id')
    user_id = request.form.get('user_id')
    temp_test = TempTest.query.filter_by(id=test_id, user_id=user_id).first()

    if not temp_test:
        return "Session expired or invalid test. Please restart the test.", 400

    # Extract the test data
    questions = temp_test.questions
    chapter = str(temp_test.chapter)
    time_spent = request.form.get('timeSpent')
    answers = request.form.get('answers')
    date = datetime.now().date()

    # Convert JSON strings to Python lists
    time_spent = json.loads(time_spent)
    answers = json.loads(answers)

    # Initialize variables for processing
    time_string = ""
    questions_ID_string = ""
    wrong_answer_string = ""
    result = []
    wrong_answers = []

    # Process the answers
    for i, question in enumerate(questions):
        questions_ID_string += f"{question['ID']}_"
        if str(answers[i]) == question["answer"]:
            result.append("1")
        else:
            result.append("0")
            wrong_answers.append(str(question['ID']))
        time_string += f"{time_spent[i]}_"

    # Clean up strings
    questions_ID_string = questions_ID_string.rstrip("_")
    time_string = time_string.rstrip("_")
    wrong_answer_string = "_".join(wrong_answers)
    score = f"{result.count('1')}/{len(result)}"


    if isinstance(chap_id, int):
        chapter_str = f"{chap_id:02d}"
    else:
        chapter_str = str(chap_id)

    # Create a new test record in the database
    new_test_record = Test(
        user_id=user_id,
        test_type=0,  
        time=date,
        knowledge=chapter_str,
        questions=questions_ID_string,
        wrong_answer=wrong_answer_string,
        result="_".join(result),
        time_result=time_string
    )
    db.session.add(new_test_record)
    db.session.commit()

    # Delete the temporary test data
    db.session.delete(temp_test)
    db.session.commit()

    task_id = str(uuid4())

    # print(chap_id)
    # Run analysis in a separate thread and pass the app object
    analysis_thread = threading.Thread(target=run_analysis_thread, args=(app, subject, chap_id, user_id, task_id, 0))
    analysis_thread.start()

    # Redirect to the review route
    return render_template("reviewTest.html", questions=questions, wrong_answer_string=wrong_answer_string, score=score, task_id=task_id)

import logging

logging.basicConfig(level=logging.DEBUG)

# Define task statuses globally
task_statuses = {}
def run_analysis_thread(app, subject, chap_id, user_id, task_id, test_type):
    with app.app_context():
        # try:
            #user_id = current_user.id
            if test_type == 3:
                task_statuses[task_id] = 'complete'
            elif test_type == 0:
                # Mark task as running
                task_statuses[task_id] = 'running'

                # Generate the analysis content
                num_of_test1 = Test.query.filter(
                    Test.questions.like(f"{subject}%")
                )
                num_of_test_done = num_of_test1.filter_by(user_id=user_id, test_type=test_type).count()
                # num_test = 10 if num_of_test_done >= 10 else num_test=num_of_test_done
                if num_of_test_done >= 10:
                    num_test = 10
                else:
                    num_test=num_of_test_done

                analyzer = generateAnalysis(subject=subject, num_chap=int(chap_id), num_test=num_test, user_id=user_id)
                analyze_content = analyzer.analyze("chapter")


            else:
                # Mark task as running
                task_statuses[task_id] = 'running'

                # Generate the analysis content
                # print(subject)
                # print('print subject roi ne')
                num_of_test1 = db.session.query(Test).filter(
                    Test.questions.like(f"{subject}%")
                )

                # Sau đó lọc tiếp theo user_id và test_type trước khi đếm số lượng
                num_of_test_done = num_of_test1.filter_by(user_id = user_id, test_type = test_type).count()

                # tests = num_of_test1.filter_by(user_id=user_id, test_type=test_type)
                # logging.debug(f"Tests query result: {tests}")

                if num_of_test_done >= 10:
                    num_test = 10
                else:
                    num_test=num_of_test_done

                # print(num_of_test1.filter_by(user_id = user_id, test_type = test_type))
                # print(subject)
                # print(chap_id)
                # print(num_test)

                # 
                # analyzer = generateAnalysis(subject=subject, num_chap=int(chap_id), num_test=num_test, user_id=user_id)
                # analyze_content = analyzer.analyze("deep")

                # get date để làm test
                drawBase = DrawChartBase(subject, int(chap_id), test_type=1, num =num_test, user_id = user_id)


                days = drawBase.time_to_do_test
                exisiting_test = Test.query.filter_by(user_id = user_id, test_type=test_type).first()
                exisiting_date = TestDate.query.filter_by(user_id = user_id, test_type = test_type, subject = subject).first()
                if isinstance(days, timedelta):
                    days = days.days  # Extract the number of days if days is a timedelta

                if not exisiting_test or not exisiting_date:

                    # Get the current date and add the number of days
                    new_date = datetime.now()
                    new_date_with_days_added = new_date + timedelta(days=days)

                    # Format the new date to 'YYYY-MM-DD'
                    new_date_str = new_date_with_days_added.date()

                    # Create a new TestDate object
                    

                    analyzer = generateAnalysis(subject=subject, num_chap=int(chap_id), num_test=num_test, user_id=user_id)
                    analyze_content = analyzer.analyze("deep")

                    current_date = datetime.now().date()
                    existing_todos = TodoList.query.filter(TodoList.user_id == user_id, TodoList.date < current_date, TodoList.subject == subject).all()
                    # thêm subject , update lại hàm filter ở trên, nếu nhỏ hơn current date của cùng subject thì xóa 


                        # Xóa các todo có date nhỏ hơn ngày hiện tại
                    for todo in existing_todos:
                        db.session.delete(todo)

                    db.session.commit()
                    todo_json = analyzer.turning_into_json()


            
                    print(todo_json)
                        # print(todo_json)
                    for todo in todo_json:
                        new_todo = TodoList(
                            todo_id=str(uuid4()),
                            user_id=user_id,
                            date=todo["date"],
                            action=todo["action"],
                            status=todo["done"],
                            subject = subject
                        )
                        db.session.add(new_todo)
                        # update date
                    new_test_date = TestDate(
                        user_id=user_id,
                        test_type=test_type,
                        subject=subject,
                        date=current_date+timedelta(days=days)
                    )
                    db.session.add(new_test_date)
                    db.session.commit()


                
                else:
                    analyzer = generateAnalysis(subject=subject, num_chap=int(chap_id), num_test=num_test, user_id=user_id)
                    analyze_content = analyzer.analyze("deep")

                    # Compare current date and existing date
                    current_date = datetime.now().date()
                    prev_date = exisiting_date.date  # Assuming it's a string like '2024-10-01'
                    # print(current_date)
                    # print(prev_date)
                    if current_date >= prev_date:
                        
                        existing_todos = TodoList.query.filter(TodoList.user_id == user_id, TodoList.date < current_date, TodoList.subject == subject).all()
                        # Xóa các todo có date nhỏ hơn ngày hiện tại
                        for todo in existing_todos:
                            db.session.delete(todo)
                        db.session.commit()
                        todo_json = analyzer.turning_into_json()

                        # print(todo_json)
                        # print(todo_json)
                        for todo in todo_json:
                            new_todo = TodoList(
                                todo_id=str(uuid4()),
                                user_id=user_id,
                                date=todo["date"],
                                action=todo["action"],
                                status=todo["done"],
                                subject = subject
                            )
                            db.session.add(new_todo)
                        # update date
                        exisiting_date.date = exisiting_date.date + timedelta(days=days)
                        db.session.commit()
            



            # print(chap_id)
            # print(num_test)
            # Update or create analysis record in the database
            existing_record = Analysis.query.filter_by(
                user_id=user_id,
                analysis_type=test_type,
                subject_id=subject,
                num_chap=chap_id
            ).first()

            
            if test_type != 3:
                if existing_record:
                    existing_record.main_text = analyze_content
                else:
                    analyze_record = Analysis(
                        user_id=user_id,
                        analysis_type=test_type,
                        subject_id=subject,
                        num_chap=chap_id,
                        main_text=analyze_content
                    )
                    db.session.add(analyze_record)

                db.session.commit()

                # Mark task as complete
                task_statuses[task_id] = 'complete'
        # except Exception as e:
        #     # Mark task as failed in case of an error
        #     task_statuses[task_id] = 'failed'
        #     print(f"Error during analysis: {e}, test_type: {test_type}")
 

@app.route("/task_status/<task_id>")
def task_status(task_id):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    status = task_statuses.get(task_id, 'pending')
    return jsonify({'status': status})



# chọn vào chương X thì nhảy qua trang đánh giá ( chapter.html ) của chương X, gọi promtChap() ra để xử lí
@app.route('/subject/<subject_id>/<chap_id>/evaluation', methods=["GET"])
def evaluate_chapter_test(subject_id,chap_id):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    # subject_id = 0
    subject_name = ''
    if subject_id == 'S1': #Toan
        subject_name = 'Toán' 
        subject = 'T'
    elif subject_id == 'S2': #Li
        subject_name = 'Lí'
        subject = 'L'
    elif subject_id == 'S3': #Hoa
        subject_name = 'Hóa'
        subject = 'H'
    elif subject_id == 0:
        return url_for('home')
    
    test_type = 0 # chapter test
    num_test = 10 # Khoa said:"the lower limit is 10"
    
    num_of_test_done = Test.query.filter_by(test_type=test_type, knowledge=chap_id).count()

    if num_of_test_done < 10: # take all finished tests if num_of_test_done is lower than 10
        num_test = num_of_test_done

    # if num_test == 0:
    #     return f"Bạn chưa làm bài test nào cho môn {subject}", 404
    
    
    existing_record = Analysis.query.filter_by(
        user_id=current_user.id,
        analysis_type=test_type,
        subject_id=subject,
        num_chap=chap_id
    ).first()
    
    if existing_record:
        analysis_result = existing_record.main_text
    else:

        # vì test purpose nên mình sẽ giữ nguyên cái này
        # theo logic thì user chưa làm bài test nào thì sẽ không có dữ liệu để phân tích
        # analyzer = generateAnalysis(subject=subject, num_chap=int(chap_id), num_test=num_test)
        # analysis_result = analyzer.analyze("chapter")
        analysis_result = "Hãy làm bài test này để có dữ liệu phân tích"
    
    #Get percent_chapter:
    grade_chapters = get_chapter_mean_list(current_user.id,subject)
    percent_chapter = grade_chapters[int(chap_id)-1]

    #QUery thred, previous result, difficulty
    thred_string = None
    query_thredhold = Progress.query.filter_by(
        user_id = current_user.id,
    ).first()
    if subject_id[1] == 1:
        thred_string = query_thredhold.threadhold_1
    elif subject_id[1] == 2:
        thred_string = query_thredhold.threadhold_2
    elif subject_id[1] == 3:
        thred_string = query_thredhold.threadhold_3
    if thred_string is None:
        max_chap = get_max_chapter(subject)
        thred = [100]*max_chap
    else:
        thred = thred_string.split('_')
    
    records = Test.query.filter(
        Test.user_id == current_user.id,
        Test.test_type == 1,
        Test.knowledge == int(chap_id),
        Test.questions.like(f'{subject}%')
    ).order_by(Test.time.desc()).limit(5).all()
    prev = []
    diff = []
    for record in records:
        question_ids = record.questions.split('_')
        results_list = record.result.split('_')
        num_ones = question_ids.count('1')
        question_count = len(results_list)
        
        # Scale the number of 1s to a grade out of 10
        grade = (num_ones / question_count) * 10
        prev.append(grade)

        # Query QAs for difficulty levels of the questions
        question_difficulties = {
        q.id: q.difficulty
        for q in QAs.query.filter(QAs.id.in_(question_ids)).all()
        }
        # Initialize counters for difficulties
        difficulty_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        correct_counts = {0: 0, 1: 0, 2: 0, 3: 0}

        # Count correct and total questions per difficulty
        for question_id, result in zip(question_ids, results_list):
            difficulty = question_difficulties.get(question_id)
            if difficulty is not None:
                difficulty_counts[difficulty] += 1
                if result == '1':  # Correct answer
                    correct_counts[difficulty] += 1

        # Calculate the percentage for each difficulty level
        percentages = {
            diff: (correct_counts[diff] / difficulty_counts[diff] * 100) if difficulty_counts[diff] > 0 else 0
            for diff in range(4)
        }
        percentage_list = [percentages[i] for i in range(4)]
        diff.append(percentage_list)
    
    print(diff)
    print(percent_chapter)
    print(thred)
    print(prev)

    num_of_test1 = db.session.query(Test).filter(
        Test.questions.like(f"{subject}%")
    )

    num_of_test_done = num_of_test1.filter_by(user_id = current_user.id, test_type = test_type).count()
    num_test = 10 if num_of_test_done >= 10 else num_of_test_done

    data_retrieve = promptChap(0, num_test, subject, current_user.id, int(chap_id))
    accu_diff, dic_ques, dic_total = data_retrieve.data.cal_accu_diff()
    chap_difficulty_percentile = data_retrieve.data.difficult_percentile_per_chap() # button-diff (nếu select chọn từ 1- 7) (% dung tung loai cau hoi tung chuong)
    results, durations, exact_time, nums = data_retrieve.data.previous_results() # button-prev (kết quả các bài test trước)

    if len(results) ==0 :
        avg_score = 0
    else:
        avg_score = int(sum(results)/len(results)*10)

    chart_data = {
        "accu_diff": accu_diff,
        "chap_difficulty_percentile": chap_difficulty_percentile,
        "results": results,
        "durations": durations,
        "exact_time": exact_time,
        "nums": nums
    }

    return render_template("chapter2.html", feedback=analysis_result, chap_id=chap_id, subject = subject, subject_id = subject_id, chart_data = chart_data,avg_score= avg_score)


# Click vào "Đánh giá" sẽ xuất hiện phân tích sâu ....
@app.route('/subject/<subject_id>/analytics', methods=["GET"])
def analyze_total_test(subject_id):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    subject_name = ''
    
    if subject_id == 'S1':  # Toán
        subject_name = 'Toán'
        subject = 'T'
    elif subject_id == 'S2':  # Lí
        subject_name = 'Lí'
        subject = 'L'
    elif subject_id == 'S3':  # Hóa
        subject_name = 'Hóa'
        subject = 'H'
    else:
        return redirect(url_for('home'))  # Redirect if subject_id is invalid
    
    test_type = 1  # Total test type
    num_of_test_done = Test.query.filter_by(test_type=test_type, user_id=current_user.id).count()

    if num_of_test_done < 10:
        num_test = num_of_test_done  # Use all tests if fewer than 10 are done
    else:
        num_test = 10  # Limit to 10 tests

    # Query the max chapter (chap_id) from the test records
    knowledge_list = db.session.query(Test.knowledge).filter(
            Test.user_id == current_user.id,
            Test.test_type == test_type,
            Test.questions.like(f"{subject}%")
        ).all()

    if knowledge_list:
            # Lấy giá trị knowledge từ các tuple
        chap_id = max(knowledge[0] for knowledge in knowledge_list)
    else:
        chap_id = 1
    # Check for an existing analysis record
    print(chap_id)

    existing_record = Analysis.query.filter_by(
        user_id=current_user.id,
        analysis_type=test_type,
        subject_id=subject,
        num_chap=chap_id
    ).first()

    if existing_record:
        analysis_result = existing_record.main_text
    else:
        analysis_result = "Hãy làm bài test này để có dữ liệu phân tích"
    
    # #Get percent_chapter:
    # grade_chapters = get_chapter_mean_list(current_user.id,subject)
    # percent_chapter = grade_chapters[int(chap_id)-1]

    # #QUery thred, previous result, difficulty
    # thred_string = None
    # query_thredhold = Progress.query.filter_by(
    #     user_id = current_user.id,
    # ).first()
    # if subject_id[1] == 1:
    #     thred_string = query_thredhold.threadhold_1
    # elif subject_id[1] == 2:
    #     thred_string = query_thredhold.threadhold_2
    # elif subject_id[1] == 3:
    #     thred_string = query_thredhold.threadhold_3
    # if thred_string is None:
    #     max_chap = get_max_chapter(subject)
    #     thred = [100]*max_chap
    # else:
    #     thred = thred_string.split('_')
    
    # records = Test.query.filter(
    #     Test.user_id == current_user.id,
    #     Test.test_type == 1,
    #     Test.questions.like(f'{subject}%')
    # ).order_by(Test.time.desc()).limit(5).all()
    # prev = []
    # diff = []
    # for record in records:
        
    #     question_ids = record.questions.split('_')
    #     results_list = record.result.split('_')
    #     num_ones = question_ids.count('1')
    #     question_count = len(results_list)
        
    #     # Scale the number of 1s to a grade out of 10
    #     grade = (num_ones / question_count) * 10
    #     prev.append(grade)

    #     # Query QAs for difficulty levels of the questions
    #     question_difficulties = {
    #     q.ID: q.difficulty
    #     for q in session.query(QAs).filter(QAs.c.ID.in_(question_ids)).all()
    #     }
    #     # Initialize counters for difficulties
    #     difficulty_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    #     correct_counts = {0: 0, 1: 0, 2: 0, 3: 0}

    #     # Count correct and total questions per difficulty
    #     for question_id, result in zip(question_ids, results_list):
    #         difficulty = question_difficulties.get(question_id)
    #         if difficulty is not None:
    #             difficulty_counts[difficulty] += 1
    #             if result == '1':  # Correct answer
    #                 correct_counts[difficulty] += 1

    #     # Calculate the percentage for each difficulty level
    #     percentages = {
    #         diff: (correct_counts[diff] / difficulty_counts[diff] * 100) if difficulty_counts[diff] > 0 else 0
    #         for diff in range(4)
    #     }
    #     percentage_list = [percentages[i] for i in range(4)]
    #     diff.append(percentage_list)
    
    # print(diff)
    # print(percent_chapter)
    # print(thred)
    # print(prev)
    # Render the evaluation template

    # subject = "T"

    num_of_test1 = db.session.query(Test).filter(
        Test.questions.like(f"{subject}%")
    )

    # làm thêm 1 trường hợp nữa, nếu k tìm ra test total thì để 0 hết


    # Sau đó lọc tiếp theo user_id và test_type trước khi đếm số lượng
    num_of_test_done = num_of_test1.filter_by(user_id = current_user.id, test_type = test_type).count()
    num_test = 10 if num_of_test_done >= 10 else num_of_test_done

    data_retrieve = promptTotal(1, num_test, subject, current_user.id)
    acuc_chaps, time_chaps = data_retrieve.data.short_total_analysis() # percent-chap (% dung tung chuong)
    accu_diff, dic_ques, dic_total = data_retrieve.data.cal_accu_diff() # button-diff (nếu select = Tất cả) (% dung tung loai cau hoi )
    chap_difficulty_percentile = data_retrieve.data.difficult_percentile_per_chap() # button-diff (nếu select chọn từ 1- 7) (% dung tung loai cau hoi tung chuong)
    results, durations, exact_time, nums = data_retrieve.data.previous_results() # button-prev (kết quả các bài test trước)

    if len(results) ==0 :
        avg_score = 0
    else:
        avg_score = int(sum(results)/len(results)*10)

    chart_data = {
        "acuc_chaps": acuc_chaps,
        "time_chaps": time_chaps,
        "accu_diff": accu_diff,
        "chap_difficulty_percentile": chap_difficulty_percentile,
        "results": results,
        "durations": durations,
        "exact_time": exact_time,
        "nums": nums
    }


    return render_template("total_eval.html", feedback=analysis_result, subject=subject, chap_id=chap_id, subject_id=subject_id, chart_data=chart_data, avg_score=avg_score)







@app.route('/subject/<subject_id>/exam-history', methods=['GET', 'POST'])
def total_exam_history(subject_id):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    subject_name = ''
    
    if subject_id == 'S1':  # Toán
        subject_name = 'Toán'
        subject = 'T'
    elif subject_id == 'S2':  # Lí  
        subject_name = 'Lí'
        subject = 'L' 
    elif subject_id == 'S3':  # Hóa
        subject_name = 'Hóa' 
        subject = 'H' 
    else:
        return redirect(url_for('home'))
    
    user_id = str(current_user.id)

    query = db.session.query(Test).filter_by(test_type=1, user_id=int(user_id)).all()
    test_list = []
    for test in query:
        num_question = 0
        num_wrong_answer = 0
        percent_of_correct_answer = 0
        num_question = test.questions.count('_') + 1
        num_wrong_answer = test.wrong_answer.count('_') + 1
        percent_of_correct_answer = round((1 - num_wrong_answer / num_question) * 100, 2)  
        test_data = {
            'test_type': test.test_type,
            'time': test.time.strftime('%d/%m/%Y'),
            'progress': percent_of_correct_answer  
        } 
        test_list.append(test_data)

    return render_template('totalHistory.html', test_list=test_list, subject_id=subject_id) 


     
@app.route('/subject/<subject_id>/<chap_id>/exam-history', methods=['GET', 'POST'])
def chapter_exam_history(subject_id,chap_id):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    subject_name = ''
    
    if subject_id == 'S1':  # Toán
        subject_name = 'Toán'
        subject = 'T'
    elif subject_id == 'S2':  # Lí  
        subject_name = 'Lí'
        subject = 'L' 
    elif subject_id == 'S3':  # Hóa
        subject_name = 'Hóa' 
        subject = 'H' 
    else:
        return redirect(url_for('home'))
    
    user_id = str(current_user.id)
    chap_id = str(chap_id)

    query = db.session.query(Test).filter_by(test_type=0, user_id=int(user_id),knowledge=chap_id).all()

    test_list = []
    for test in query:
        num_question = 0
        num_wrong_answer = 0
        percent_of_correct_answer = 0
        num_question = test.questions.count('_') + 1
        num_wrong_answer = test.wrong_answer.count('_') + 1
        percent_of_correct_answer = round((1 - num_wrong_answer / num_question) * 100, 2)  
        test_data = {
            'test_type': test.test_type,
            'time': test.time.strftime('%d/%m/%Y'),
            'chapter': test.knowledge,
            'progress': percent_of_correct_answer  
        } 
        test_list.append(test_data) 

    return render_template('chapterHistory.html', test_list=test_list, subject_id=subject_id, chap_id=chap_id) 

 
import os
from openai import OpenAI
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

@app.route('/subject/<subject_id>/<chap_id>/review-chapter', methods=['GET', 'POST'])
def review_chapter(subject_id, chap_id):
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    chapter_data = {
        "S3": {
            "01": {"title": "Este và Lipit", "img": "/static/chemistry/c1.jpg"},
            "02": {"title": "Cacbohidrat", "img": "/static/chemistry/c2.jpg"},
            "03": {"title": "Amin, Amino axit và protein", "img": "/static/chemistry/c3.png"},
            "04": {"title": "Polime và vật liệu polime", "img": "/static/chemistry/c4.png"},
            "05": {"title": "Đại cương về kim loại", "img": "/static/chemistry/c5.png"},
            "06": {"title": "Kim loại kiềm - kiềm thổ - nhôm", "img": "/static/chemistry/c6.png"},
            "07": {"title": "Crom - Sắt - Đồng", "img": "/static/chemistry/c7.png"},
        },
        "S2": {
            "01": {"title": "Dao động cơ", "img": "/static/physics/c1.jpg"},
            "02": {"title": "Sóng cơ và sóng âm", "img": "/static/physics/c2.jpg"},
            "03": {"title": "Dòng điện xoay chiều", "img": "/static/physics/c3.jpg"},
            "04": {"title": "Giao động và sóng điện từ", "img": "/static/physics/c4.jpg"},
            "05": {"title": "Sóng ánh sáng", "img": "/static/physics/c5.png"},
            "06": {"title": "Lượng tử ánh sáng", "img": "/static/physics/c6.png"},
            "07": {"title": "Hạt nhân nguyên tử", "img": "/static/physics/c7.png"},
        },
        "S1": {
            "01": {"title": "Ứng dụng đạo hàm để khảo sát và vẽ đồ thị của hàm số", "img": "/static/maths/c1.jpeg"},
            "02": {"title": "Hàm số lũy thừa, hàm số mũ và hàm số logarit", "img": "/static/maths/c2.jpg"},
            "03": {"title": "Nguyên hàm. Tích phân và ứng dụng", "img": "/static/maths/c3.jpg"},
            "04": {"title": "Số phức", "img": "/static/maths/c4.jpg"},
            "05": {"title": "Khối đa diện", "img": "/static/maths/c5.jpg"},
            "06": {"title": "Mặt nón, mặt trụ, mặt cầu", "img": "/static/maths/c6.jpg"},
            "07": {"title": "Phương pháp tọa độ trong không gian", "img": "/static/maths/c7.jpg"},
        }
    }
    if subject_id in chapter_data and chap_id in chapter_data[subject_id]:
        chapter_title = chapter_data[subject_id][chap_id]["title"]
        img_src = chapter_data[subject_id][chap_id]["img"]
        data = chapter_title  
    else:
        chapter_title = "Chapter Not Found"
        img_src = ""
        data = "No data available for this chapter."

    return render_template("chatbot.html", subject_id=subject_id, chap_id=chap_id, chapter_title=chapter_title, img_src=img_src)

@app.route("/api", methods=["POST"])
def api():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    if current_user.uni_select == 0:
        return redirect(url_for('select_uni'))
    try:
        data = request.get_json()
        print("Received data:", data)

        message = data.get("message")
        subject_id = data.get("subject_id")
        chap_id = data.get("chap_id")

        print("subject_id:", subject_id)
        print("chap_id:", chap_id)

        if not message or not subject_id or not chap_id:
            return jsonify({"response": "Thiếu dữ liệu trong yêu cầu."}), 400

        # Định dạng chap_id thành chuỗi hai chữ số
        chap_id_formatted = chap_id.zfill(2)

        # Truy vấn cơ sở dữ liệu
        knowledge_data = Knowledge.query.filter_by(
            id_subject=subject_id, num_chap=chap_id_formatted
        ).first()

        if knowledge_data is None:
            return jsonify({"response": "Không tìm thấy dữ liệu cho môn học và chương này."}), 404
 
        # Gọi API OpenAI
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"Bạn là 1 gia sư giải thích lý thuyết bài học cho học sinh, sau đây là phần lý thuyết của bài học học sinh chuẩn bị hỏi: {knowledge_data.latex_text}"
                    },
                    {"role": "user", "content": message}
                ]
            )
        except Exception as e:
            print("Error during OpenAI API call:", e)
            return jsonify({"response": "Lỗi khi giao tiếp với dịch vụ AI."}), 500

        if completion.choices and completion.choices[0].message:
            content = completion.choices[0].message.content
            return jsonify({"response": content})
        else:
            return jsonify({"response": "Không thể tạo phản hồi."}), 500

    except Exception as e:
        print("Error in /api route:", e)
        return jsonify({"response": "Máy chủ gặp lỗi khi xử lý yêu cầu."}), 500
















# # Getting-started route
# @app.route("/getting-started", methods=("GET", "POST"), strict_slashes=True)
# def getting_started():
#     if current_user.is_authenticated == False:
#         return redirect(url_for('login'))
    
#     form = getting_started_form()

#     if form.validate_on_submit():
#         value1 = form.value1.data
#         value2 = form.value2.data
#         value3 = form.value3.data
#         baseprogress = f"{value1}_{value2}_{value3}"

#         user_id = current_user.id 

#         existing_progress = Progress.query.filter_by(user_id=user_id).first()
#         if existing_progress != None:
#             existing_progress.baseprogress = baseprogress
#             existing_progress.progress1 = "0"
#             existing_progress.progress2 = "0"
#             existing_progress.progress3 = "0"
#         else:
#             new_progress = Progress(
#                 user_id=user_id,
#                 base_progress=baseprogress,
#                 progress_1="0",
#                 progress_2="0",
#                 progress_3="0"
#             )
#             db.session.add(new_progress)
#         db.session.commit()
#         return redirect(url_for('index'))

#     return render_template("getting_started.html", form=form)


# # Progress route
# @app.route("/progress", methods=("GET", "POST"), strict_slashes=False)
# def progress():
#     if current_user.is_authenticated == False:
#         return redirect(url_for('login'))

#     user_id = current_user.id 
#     user_progress = Progress.query.filter_by(user_id=user_id).first()
#     print(user_progress.progress_1)
#     if user_progress != None:
#         progress1_values = [int(x) for x in user_progress.progress_1.split('_')]
#         progress2_values = [int(x) for x in user_progress.progress_2.split('_')]
#         progress3_values = [int(x) for x in user_progress.progress_3.split('_')]
#         return render_template(
#             "progress.html",
#             title="Tiến trình",
#             total_pro_1 = progress1_values[0],
#             progress_1=progress1_values[1:],
#             total_pro_2 = progress2_values[0],
#             progress_2=progress2_values[1:],
#             total_pro_3 = progress3_values[0],
#             progress_3=progress3_values[1:]
#         )
#     else:
#         return render_template("progress.html", title="Tiến trình", progress=None)
    

if __name__ == "__main__":
    app.run(debug=True) 