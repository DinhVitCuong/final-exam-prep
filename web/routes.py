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

from app import create_app, db, login_manager, bcrypt
from models import User, Progress, Test, Universities, QAs, Subject, TodoList, SubjectCategory
from forms import login_form,register_form, test_selection_form, select_univesity_form
from test_classes_sql import TestChap, TestTotal, pr_br_rcmd


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
    return render_template("home.html", title="Trang chủ", university=university)



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
                existing_progress = Progress.query.filter_by(user_id=current_user.id).first()
                if existing_progress is not None:
                    existing_progress.user_major_uni = selected_university.id
                    existing_progress.user_subject_cat = form.subject_category.data
                    existing_progress.target_progress = target_progress
                else:
                    new_progress = Progress(
                        user_id = current_user.id,
                        user_major_uni = selected_university.id,
                        user_subject_cat = form.subject_category.data,
                        target_progress = target_progress
                    )
                    db.session.add(new_progress)
                current_user.uni_select = 1
                db.session.commit()
            print("check clicked")
            return render_template("select_uni.html", form=form, uni_name= uni_name, score= majors_score, current_slide=current_slide)

    # Initialize with an empty list if no submission
    form.major.choices = []
    form.university.choices = []

    return render_template("select_uni.html", form=form,current_slide=0)


app.route('/subject/<subject_id>')
def subject(subject_id):
    subject = 0
    if subject_id == 'S1':
        subject = 1
    elif subject_id == 'S2':
        subject = 2
    elif subject_id == 'S3':
        subject = 3
    
    return render_template('subject.html', subject=subject)

# #Multiple_choice_test route
# @app.route("/test-select", methods=("GET", "POST"), strict_slashes=False)
# def test_select():
#     subjects_and_chapters = {
#         "Math": [("chapter1", "Algebra"), ("chapter2", "Geometry"), ("chapter3", "Calculus")],
#         "Science": [("chapter1", "Physics"), ("chapter2", "Chemistry"), ("chapter3", "Biology")],
#         "History": [("chapter1", "Ancient"), ("chapter2", "Medieval"), ("chapter3", "Modern")]
#     }
    
#     form = test_selection_form()
#     form.subject.choices = [(subject, subject) for subject in subjects_and_chapters.keys()]

#     if form.validate_on_submit():
#         test_type = form.test_type.data
#         selected_subject = form.subject.data
#         chapters = subjects_and_chapters.get(selected_subject, [])

#         if test_type == "total":
#             selected_chapters = form.total_chapters.data
#             if len(selected_chapters) >= 2:
#                 return redirect(url_for('total_test', chapters=",".join(selected_chapters)))
#             else:
#                 return "Please select at least two chapters for the Total Test.", 400

#         elif test_type == "chapter":
#             selected_chapter = form.chapter.data
#             return redirect(url_for('chapter_test', chapter=selected_chapter))
        
#         elif test_type == "practice":
#             selected_chapter = form.chapter.data
#             return redirect(url_for('practice_test', chapter=selected_chapter))

#     # Set chapters based on the subject selected (if any)
#     selected_subject = form.subject.data
#     chapters = subjects_and_chapters.get(selected_subject, [])
#     form.total_chapters.choices = chapters
#     form.chapter.choices = chapters

#     return render_template("test_select.html", form=form)



#haven't debug yet

@app.route("/chapter-test")
def chapter_test():
    chapter = request.args.get("chapter")
    # Process chapter test with selected chapter
    return f"Starting Chapter Test with chapter: {chapter}" 

@app.route("/practice-test")
def total_test():
    chapters = request.args.get("chapters")
    # Process total test with selected chapters
    return f"Starting Total Test with chapters: {chapters}"

@app.route("/total-test")
def total_test():
    chapters = request.args.get("chapters")
    # Process total test with selected chapters
    return f"Starting Total Test with chapters: {chapters}"


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
