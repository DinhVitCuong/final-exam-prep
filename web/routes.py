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
from models import User, Progress, Test, Universities, QAs, Subject, TodoList, SubjectCategory, TempTest, Analysis, TestDate
from forms import login_form,register_form, test_selection_form, select_univesity_form,QuizForm
from test_classes_sql import TestChap, TestTotal, pr_br_rcmd
from gpt_integrate_sql import promptCreation,promptTotal,promptChap,generateAnalysis
from data_retriever_sql import DrawChartBase
from datetime import datetime
import time
from uuid import uuid4

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
    return render_template("home.html", title="Trang chủ", university=university, subject=subject)



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

    # Store the test data in the database
    temp_test = TempTest(
        id=test_id,
        user_id=current_user.id,
        subject=subject,
        questions=questions,
        chapter=chapter,
        time_limit=time_limit,
        rate=rate
    )
    db.session.add(temp_test)
    db.session.commit()

    # Pass the test ID to the template
    return render_template('exam.html', subject=subject, time_limit=time_limit, questions=questions, test_id=test_id, chap_id = chapter)
        
@app.route("/total-test/<chap_id>/<subject>", methods=["POST"])
def total_test_post(chap_id, subject):
    # Existing logic for processing answers
    test_id = request.form.get('test_id')
    temp_test = TempTest.query.filter_by(id=test_id, user_id=current_user.id).first()

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
        user_id=current_user.id,
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
    analysis_thread = threading.Thread(target=run_analysis_thread, args=(app, subject, chap_id, current_user.id, task_id, 1))
    analysis_thread.start()


    # Redirect to the review route
    return render_template("reviewTest.html", questions=questions, wrong_answer_string=wrong_answer_string, score=score, task_id=task_id)
    
@app.route('/subject/<subject_id>', methods=["GET", "POST"])
def subject(subject_id):
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
    
    # Pass subject_id to the template
    return render_template(
        'subject.html', 
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



@app.route("/practice-test/<subject>", methods=["GET", "POST"])
def practice_test(subject):
    # Xác định chapter theo subject
    if subject == "M":
        chapter_count = 7
    elif subject == "L":
        chapter_count = 7
    else:
        chapter_count = 8

    time_limit = 45  
    rate = [40, 20, 30, 10]     
    
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

        # Store the test data in the database
        temp_test = TempTest(
            id=test_id,
            user_id=current_user.id,
            subject=subject,
            questions=questions,
            chapter='05',
            time_limit=time_limit,
            rate=rate
        )
        db.session.add(temp_test)
        db.session.commit()

        return render_template('practice_exam.html', subject=subject, time_limit=time_limit, questions=questions, test_id=test_id)

    elif request.method == "POST":
        # Retrieve the test ID from the form data
        test_id = request.form.get('test_id')

        # Retrieve the stored test data using the test ID
        temp_test = TempTest.query.filter_by(id=test_id, user_id=current_user.id).first()
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

        # Redirect to the review route
        return render_template("reviewTest.html", questions=questions, wrong_answer_string=wrong_answer_string, score=score)


@app.route("/chapter-test/<chap_id>/<subject>", methods=["GET"])
def chapter_test(chap_id, subject):  # Nhận trực tiếp cả chap_id và subject từ URL
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

    # Store the test data in the database
    temp_test = TempTest(
        id=test_id,
        user_id=current_user.id,
        subject=subject,
        questions=questions,
        chapter=chap_id,
        time_limit=time_limit,
        rate=rate
    )
    db.session.add(temp_test)
    db.session.commit()

    # Pass the test ID to the template
    return render_template('chapter_exam.html', subject=subject, time_limit=time_limit, questions=questions, test_id=test_id, chap_id = chap_id)

        
    
@app.route("/chapter-test/<chap_id>/<subject>", methods=["POST"])
def chapter_test_post(chap_id, subject):
    # Existing logic for processing answers
    test_id = request.form.get('test_id')
    temp_test = TempTest.query.filter_by(id=test_id, user_id=current_user.id).first()

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
        user_id=current_user.id,
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

    print(chap_id)
    # Run analysis in a separate thread and pass the app object
    analysis_thread = threading.Thread(target=run_analysis_thread, args=(app, subject, chap_id, current_user.id, task_id, 0))
    analysis_thread.start()

    # Redirect to the review route
    return render_template("reviewTest.html", questions=questions, wrong_answer_string=wrong_answer_string, score=score, task_id=task_id)


# Define task statuses globally
task_statuses = {}

def run_analysis_thread(app, subject, chap_id, user_id, task_id, test_type):
    with app.app_context():
        try:
            #user_id = current_user.id
            if test_type == 0:
                # Mark task as running
                task_statuses[task_id] = 'running'

                # Generate the analysis content
                
                num_of_test_done = Test.query.filter_by(test_type=test_type, knowledge=chap_id).count()
                num_test = 10 if num_of_test_done >= 10 else num_of_test_done

                analyzer = generateAnalysis(subject=subject, num_chap=int(chap_id), num_test=num_test)
                analyze_content = analyzer.analyze("chapter")
            else:
                # Mark task as running
                task_statuses[task_id] = 'running'

                # Generate the analysis content
                
                num_of_test_done = Test.query.filter_by(test_type=test_type).count()
                num_test = 10 if num_of_test_done > 10 else num_of_test_done
                
                print(chap_id)
                print(num_test)
                analyzer = generateAnalysis(subject=subject, num_chap=int(chap_id), num_test=num_test)
                analyze_content = analyzer.analyze("deep")

                # get date để làm test
                drawBase = DrawChartBase(subject, int(chap_id), test_type=1, num =num_test)
                days = drawBase.time_to_do_test
                exisiting_test = Test.query.filter_by(test_type=test_type).first()
                exisiting_date = TestDate.query.filter_by(user_id = user_id, test_type = test_type).first()
                if isinstance(days, timedelta):
                    days = days.days  # Extract the number of days if `days` is a timedelta

                if not exisiting_test or not exisiting_date:
                    # Get the current date and add the number of days
                    new_date = datetime.now()
                    new_date_with_days_added = new_date + timedelta(days=days)

                    # Format the new date to 'YYYY-MM-DD'
                    new_date_str = new_date_with_days_added.date()

                    # Create a new TestDate object
                    new_test_date = TestDate(
                        user_id=user_id,
                        test_type=test_type,
                        subject=subject,
                        date=new_date_str
                    )
                    db.session.add(new_test_date)
                    db.session.commit()

                else:
                    # Compare current date and existing date
                    current_date = datetime.now().date()
                    prev_date = exisiting_date.date  # Assuming it's a string like '2024-10-01'
                    # print(current_date)
                    # print(prev_date)
                    if current_date >= prev_date:

                        existing_todos = TodoList.query.filter(TodoList.user_id == user_id, TodoList.date < current_date).all()
                        # Xóa các todo có date nhỏ hơn ngày hiện tại
                        for todo in existing_todos:
                            db.session.delete(todo)
                        db.session.commit()
                        todo_json = analyzer.turning_into_json()

                        print(todo_json)
                        for todo in todo_json:
                            new_todo = TodoList(
                                todo_id=str(uuid4()),
                                user_id=user_id,
                                date=todo["date"],
                                action=todo["action"],
                                status=todo["done"]
                            )
                            db.session.add(new_todo)
                        exisiting_date.date = current_date + timedelta(days=days)
                        db.session.commit()
                        

                # to do list


            print(chap_id)
            print(num_test)
            # Update or create analysis record in the database
            existing_record = Analysis.query.filter_by(
                user_id=user_id,
                analysis_type=test_type,
                subject_id=subject,
                num_chap=chap_id
            ).first()

            
            
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
        except Exception as e:
            # Mark task as failed in case of an error
            task_statuses[task_id] = 'failed'
            print(f"Error during analysis: {e}, test_type: {test_type}")


@app.route("/task_status/<task_id>")
def task_status(task_id):
    status = task_statuses.get(task_id, 'pending')
    return jsonify({'status': status})



# chọn vào chương X thì nhảy qua trang đánh giá ( chapter.html ) của chương X, gọi promtChap() ra để xử lí
@app.route('/subject/<subject_id>/<chap_id>/evaluation', methods=["GET"])
def evaluate_chapter_test(subject_id,chap_id):
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
    
    return render_template("chapter.html", feedback=analysis_result, chap_id=chap_id, subject = subject, subject_id = subject_id)


# Click vào "Đánh giá" sẽ xuất hiện phân tích sâu ....
@app.route('/subject/<subject_id>/analytics', methods=["GET"])
def analyze_total_test(subject_id):
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
    chap_id_list = db.session.query(Test.knowledge).filter_by(
        user_id=current_user.id,
        test_type=test_type
    ).all()
    if chap_id_list != []:
        # handle error neu nhu ko co
        chap_id = max(int(a[0]) for a in chap_id_list)  # Extract max chap_id
    else:
        return "Loi roi dume"
    # Check for an existing analysis record
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

    # Render the evaluation template
    return render_template("total_eval.html", feedback=analysis_result, subject=subject, chap_id=chap_id, subject_id = subject_id)




























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
