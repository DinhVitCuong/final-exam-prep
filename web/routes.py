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


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from app import create_app,db,login_manager,bcrypt
from models import User, Progress, Test
from forms import login_form,register_form, getting_started_form, test_selection_form, select_univesity_form


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

    user_id = current_user.id 
    user_progress = Progress.query.filter_by(user_id=user_id).first()
    print(user_progress)
    return render_template("index.html",title="Home", user_progress = user_progress)


# Login route
@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
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
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data
            
            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
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
        return redirect(url_for("select-uni"))
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


# #Home route
# @app.route("/home", methods=("GET", "POST"), strict_slashes=False)
# def home():
#     if current_user.is_authenticated == False:
#         return redirect(url_for('login'))

#     user_id = current_user.id 
#     return render_template("getting_started.html", title="Trang chủ")



@app.route("/select-uni", methods=("GET","POST"), strict_slashes=True)
def select_uni():
    form = select_univesity_form()
    
    universities = {
        ('low', 'us', 'A'): ['Community College of A', 'Budget State University A'],
        ('medium', 'us', 'A'): ['Mid-tier A University', 'Affordable Institute of A'],
        ('high', 'us', 'A'): ['Elite Institute of A', 'Premier A University'],
        ('low', 'uk', 'B'): ['Budget B College', 'Affordable B Academy'],
        ('medium', 'uk', 'B'): ['Moderate B University', 'Cultural B Institute'],
        ('high', 'uk', 'B'): ['Prestigious B University', 'Royal B Academy'],
        # Add more combinations as needed...
    }

    if form.validate_on_submit():
        selected_budget = form.budget.data.lower()
        selected_locations = form.location.data  # List of selected locations
        selected_majors = form.major.data        # List of selected majors

        if selected_budget.isdigit():
            if int(selected_budget) < 5000:
                budget_key = 'low'
            elif 5000 <= int(selected_budget) < 15000:
                budget_key = 'medium'
            else:
                budget_key = 'high'
        else:
            budget_key = 'low'  # Default to low if invalid input
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 
#Need re-coding
        available_universities = []
        if selected_locations is not None:
            for location in selected_locations:
                for major in selected_majors:
                    key = (budget_key, location, major)
                    available_universities.extend(universities.get(key, []))
        # if selected_majors is not None:
        #     for major

        form.university.choices = [(uni, uni) for uni in available_universities]

        if 'check' in request.form:
            # Handle the 'Check' button click
            return render_template("select_uni.html", form=form)

        if 'submit' in request.form and form.university.data:
            # Handle the 'Submit' button click
            selected_university = form.university.data
            return redirect(url_for('index', university=selected_university))

    # Initialize with an empty list if no submission has occurred yet
    form.university.choices = []

    return render_template("select_uni.html", form=form)


# Getting-started route
@app.route("/getting-started", methods=("GET", "POST"), strict_slashes=True)
def getting_started():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    
    form = getting_started_form()

    if form.validate_on_submit():
        value1 = form.value1.data
        value2 = form.value2.data
        value3 = form.value3.data
        baseprogress = f"{value1}_{value2}_{value3}"

        user_id = current_user.id 

        existing_progress = Progress.query.filter_by(user_id=user_id).first()
        if existing_progress != None:
            existing_progress.baseprogress = baseprogress
            existing_progress.progress1 = "0"
            existing_progress.progress2 = "0"
            existing_progress.progress3 = "0"
        else:
            new_progress = Progress(
                user_id=user_id,
                base_progress=baseprogress,
                progress_1="0",
                progress_2="0",
                progress_3="0"
            )
            db.session.add(new_progress)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template("getting_started.html", form=form)



# Progress route
@app.route("/progress", methods=("GET", "POST"), strict_slashes=False)
def progress():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))

    user_id = current_user.id 
    user_progress = Progress.query.filter_by(user_id=user_id).first()
    print(user_progress.progress_1)
    if user_progress != None:
        progress1_values = [int(x) for x in user_progress.progress_1.split('_')]
        progress2_values = [int(x) for x in user_progress.progress_2.split('_')]
        progress3_values = [int(x) for x in user_progress.progress_3.split('_')]
        return render_template(
            "progress.html",
            title="Tiến trình",
            total_pro_1 = progress1_values[0],
            progress_1=progress1_values[1:],
            total_pro_2 = progress2_values[0],
            progress_2=progress2_values[1:],
            total_pro_3 = progress3_values[0],
            progress_3=progress3_values[1:]
        )
    else:
        return render_template("progress.html", title="Tiến trình", progress=None)
    


#Multiple_choice_test route
@app.route("/test-select", methods=("GET", "POST"), strict_slashes=False)
def test_select():
    subjects_and_chapters = {
        "Math": [("chapter1", "Algebra"), ("chapter2", "Geometry"), ("chapter3", "Calculus")],
        "Science": [("chapter1", "Physics"), ("chapter2", "Chemistry"), ("chapter3", "Biology")],
        "History": [("chapter1", "Ancient"), ("chapter2", "Medieval"), ("chapter3", "Modern")]
    }
    
    form = test_selection_form()
    form.subject.choices = [(subject, subject) for subject in subjects_and_chapters.keys()]

    if form.validate_on_submit():
        test_type = form.test_type.data
        selected_subject = form.subject.data
        chapters = subjects_and_chapters.get(selected_subject, [])

        if test_type == "total":
            selected_chapters = form.total_chapters.data
            if len(selected_chapters) >= 2:
                return redirect(url_for('total_test', chapters=",".join(selected_chapters)))
            else:
                return "Please select at least two chapters for the Total Test.", 400

        elif test_type == "chapter":
            selected_chapter = form.chapter.data
            return redirect(url_for('chapter_test', chapter=selected_chapter))

    # Set chapters based on the subject selected (if any)
    selected_subject = form.subject.data
    chapters = subjects_and_chapters.get(selected_subject, [])
    form.total_chapters.choices = chapters
    form.chapter.choices = chapters

    return render_template("test_select.html", form=form)



#haven't debug yet
@app.route("/total-test")
def total_test():
    chapters = request.args.get("chapters")
    # Process total test with selected chapters
    return f"Starting Total Test with chapters: {chapters}"

@app.route("/chapter-test")
def chapter_test():
    chapter = request.args.get("chapter")
    # Process chapter test with selected chapter
    return f"Starting Chapter Test with chapter: {chapter}" 

if __name__ == "__main__":
    app.run(debug=True)
