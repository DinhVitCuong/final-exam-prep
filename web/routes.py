from flask import (
    Flask,
    render_template,
    redirect,
    flash,
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
from models import User, Progress
from forms import login_form,register_form, getting_started_form


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


# #Home route
# @app.route("/home", methods=("GET", "POST"), strict_slashes=False)
# def home():
#     if current_user.is_authenticated == False:
#         return redirect(url_for('login'))

#     user_id = current_user.id 
#     return render_template("getting_started.html", title="Trang chủ")


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

    return render_template("getting_started.html", form=form)


#Multiple_choice_test route
@app.route("/test-select", methods=("GET", "POST"), strict_slashes=False)
def test_select():
    
    return render_template("test_select.html")
if __name__ == "__main__":
    app.run(debug=True)
