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
from models import User, Progress, Test, Universities, QAs, Subject, TodoList, SubjectCategory
from forms import login_form,register_form, test_selection_form, select_univesity_form,QuizForm
from test_classes_sql import TestChap, TestTotal, pr_br_rcmd
from gpt_integrate_sql import promptCreation,promptTotal,promptChap,generateAnalysis

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




@app.route("/total-test/<subject>", methods=["GET", "POST"])  
def total_test(subject):  
    if subject == "M":
        chapter = 7
    elif subject == "L":
        chapter = 7
    else:
        chapter = 8

    time_limit = 90  # Giới hạn thời gian cho bài kiểm tra, tính bằng phút
    rate = [40, 30, 20, 10]  # Tỉ lệ các câu hỏi theo từng mức độ
    test_total = TestTotal(subject, chapter)
    # questions = test_total.create_test(rate)
    questions = [{"ID": q.id, "question": q.question, "options": q.options, "answer": q.answer} for q in test_total.create_test(rate)]
    # Kiểm tra nếu phương thức HTTP là POST (khi người dùng gửi câu trả lời)
    if request.method == "POST":
        time_spent = request.form.get('timeSpent')
        answers = request.form.get('answers')
        date = request.form.get('date') 

        # Convert từ chuỗi JSON sang danh sách Python
        time_spent = json.loads(time_spent)
        answers = json.loads(answers)

        time_string = ""
        questions_ID_string = ""
        wrong_answer_string = ""    
        chapters = ""
        result = []  
        wrong_answers = []

        # Xử lý dữ liệu câu hỏi
        for i in range(chapter):
            chapters += f"{i+1}_"
        for i, question in enumerate(questions):
            questions_ID_string += f"{question.id}_"
            result.append(str(answers[i]))
            time_string += f"{time_spent[i]}_"
            
            if answers[i] == 0:
                wrong_answers.append(str(question.id))

        # Xóa dấu gạch dưới cuối chuỗi
        questions_ID_string = questions_ID_string.rstrip("_")
        time_string = time_string.rstrip("_")
        chapters = chapters.rstrip("_")
        wrong_answer_string = "_".join(wrong_answers)

        # Tạo bản ghi mới trong bảng Test
        new_test_record = Test(
            user_id=current_user.id,
            test_type=1,  # Loại bài kiểm tra tổng
            time=date,
            knowledge=chapters,
            questions=questions_ID_string,
            wrong_answer=wrong_answer_string,
            result="_".join(result),  # Chuỗi kết quả dạng 0_1_0...
            time_result=time_string  # Chuỗi thời gian làm từng câu
        )
        db.session.add(new_test_record)
        db.session.commit()

        # Sau khi hoàn thành, chuyển hướng về trang chủ
        return render_template('home.html')

    # Nếu không phải là POST, render trang thi với câu hỏi
    return render_template('exam.html', subject=subject, time_limit=time_limit, questions=questions)

@app.route('/subject/<subject_id>', methods=["GET", "POST"])
def subject(subject_id):
    subject_name = ''
    if subject_id == 'S1':  # Toán
        subject_name = 'Toán'
        subject = 'M'
    elif subject_id == 'S2':  # Lí
        subject_name = 'Lí'
        subject = 'L'
    elif subject_id == 'S3':  # Hóa
        subject_name = 'Hóa'
        subject = 'H'
    else:
        return redirect(url_for('home'))  
    
    
    chapter_numbers = (
    QAs.query
    .filter(QAs.id.like(f'{subject}%'))
    .with_entities(db.func.substr(QAs.id, 2, 2).label('chapter_number'))  
    .distinct()
    .all()
)

    chapter_numbers_list = [f"{int(row.chapter_number):02}" for row in chapter_numbers]

    # Convert the results to a list of chapter numbers
    chapter_numbers_list = [f"{int(row.chapter_number):02}" for row in chapter_numbers]
    
    return render_template('subject.html', subject_name=subject_name, subject=subject, chapter_numbers_list=chapter_numbers_list)

@app.route("/chapter-test/<chap_id>")
def chapter_test(chap_id):
    subject = request.args.get('subject')
    time_limit = 45 #Minute
    rate = [40, 30, 20, 10]
    test_chap = TestChap(subject, chap_id)
    questions= test_chap.create_test(rate)
    if request.method == "POST":
        
        time_spent = request.form.get('timeSpent')
        answers = request.form.get('answers')
        date = request.form.get('date')
        # Convert from JSON string back to Python lists
        
        time_spent = json.loads(time_spent)
        answers = json.loads(answers)
        time_string = ""
        questions_ID_string = ""
        wrong_answer_string = ""
        result = []
        wrong_answers = []
        for i, question in enumerate(questions):
            questions_ID_string += f"{question.ID}_"
            result.append(str(answers[i]))
            time_string += f"{time_spent[i]}_"
            
            if answers[i] == 0:
                wrong_answers.append(str(question.ID))

        # Remove trailing underscores from strings
        questions_ID_string = questions_ID_string.rstrip("_")
        time_string = time_string.rstrip("_")
        wrong_answer_string = "_".join(wrong_answers)

        # Create a new Test record
        new_test_record = Test(
            user_id=current_user.id,
            test_type=0,  # 0 for Chapter test
            time=date,
            knowledge=chap_id,
            questions=questions_ID_string,
            wrong_answer=wrong_answer_string,
            result="_".join(result),  # Format 0_1_0...
            time_result=time_string  # Format time1_time2_time3...
        )
        db.session.add(new_test_record)
        db.session.commit()
        # Redirect to another page or render a home template
        return render_template('home.html')


    return render_template('exam.html', subject=subject, time_limit = time_limit, questions=questions)

@app.route("/practice-test/<subject>")
def practice_test(subject):
    if subject == "M":
        chapter = 7 
    elif subject == "L":
        chapter = 7
    else:
        chapter = 8
    time_limit = 90 #Minute
    rate = [40, 30, 20, 10]
    test_prac = pr_br_rcmd(subject, 5, 1)
    questions = test_prac.question_prep
    if request.method == "POST":
        
        time_spent = request.form.get('timeSpent')
        answers = request.form.get('answers')
        date = request.form.get('date')
        # Convert from JSON string back to Python lists
        time_spent = json.loads(time_spent)
        answers = json.loads(answers)
        time_string = ""
        questions_ID_string = ""
        wrong_answer_string = ""
        chapters = ""
        result = []
        wrong_answers = []
        for i in range(chapter):
            chapters += f"{i+1}_"
        for i, question in enumerate(questions):
            questions_ID_string += f"{question.ID}_"
            result.append(str(answers[i]))
            time_string += f"{time_spent[i]}_"
            
            if answers[i] == 0:
                wrong_answers.append(str(question.ID))

        # Remove trailing underscores from strings
        questions_ID_string = questions_ID_string.rstrip("_")
        time_string = time_string.rstrip("_")
        chapters = chapters.rstrip("_")
        wrong_answer_string = "_".join(wrong_answers)

        # Create a new Test record
        new_test_record = Test(
            user_id=current_user.id,
            test_type=3,  
            time=date,
            knowledge=chapters,
            questions=questions_ID_string,
            wrong_answer=wrong_answer_string,
            result="_".join(result),  # Format 0_1_0...
            time_result=time_string  # Format time1_time2_time3...
        )
        db.session.add(new_test_record)
        db.session.commit()
        # Redirect to another page or render a home template
        return render_template('home.html')


    return render_template('exam.html', subject=subject, time_limit = time_limit, questions=questions)


# chọn vào chương X thì nhảy qua trang đánh giá ( chapter.html ) của chương X, gọi promtChap() ra để xử lí
@app.route('/subject/<subject_id>/<chap_id>/evaluation', methods=["GET"])
def evaluate_chapter_test(subject_id,chap_id):
    subject_id = 0
    subject_name = ''
    if subject_id == 'S1': #Toan
        subject_name = 'Toán'
        subject = 'M'
    elif subject_id == 'S2': #Li
        subject_name = 'Lí'
        subject = 'L'
    elif subject_id == 'S3': #Hoa
        subject_name = 'Hóa'
        subject = 'H'
    elif subject_id == 0:
        return url_for('home')
    
    type_test = 0 # chapter test
    num_test = 10 # Khoa said:"the lower limit is 10"
    
    num_of_test_done = Test.query.filter_by(subject=subject, type_test=type_test, knowledge=chap_id).count()

    if num_of_test_done < 10: # take all finished tests if num_of_test_done is lower than 10
        num_test = num_of_test_done

    if num_test == 0:
        return f"Bạn chưa làm bài test nào cho môn {subject}", 404
    
    analyzer = promptChap(type_test,num_test,subject,num_chap=chap_id)
    analysis_result = analyzer.chap_analysis()

    return render_template("chapter.html", feedback=analysis_result)


# Click vào "Đánh giá" sẽ xuất hiện phân tích sâu ....
@app.route('/subject/<subject_id>/analytics', methods=["GET"])
def analize_total_test(subject_id):
    subject_id = 0
    subject_name = ''
    if subject_id == 'S1': #Toan
        subject_name = 'Toán'
        subject = 'M'
    elif subject_id == 'S2': #Li
        subject_name = 'Lí'
        subject = 'L'
    elif subject_id == 'S3': #Hoa
        subject_name = 'Hóa'
        subject = 'H'
    elif subject_id == 0:
        return url_for('home')
    type_test = 1 # chapter test
    
    analyzer = generateAnalysis(subject=subject, num_chap=0) # num_chap = 0 means total test
    analysis_result = analyzer.chap_analysis()

    return render_template("chapter.html", feedback=analysis_result)



























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
