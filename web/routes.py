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
    return render_template("index.html",title="Home")


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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/progress", methods=("GET", "POST"), strict_slashes=False)
def progress():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_progress = Progress.query.filter_by(user_id=user_id).first()

    if user_progress:
        progress1_values = [int(x) for x in user_progress.progress1.split(';')]
        progress2_values = [int(x) for x in user_progress.progress2.split(';')]
        progress3_values = [int(x) for x in user_progress.progress3.split(';')]
        return render_template(
            "progress.html",
            title="Tiến trình",
            progress1=progress1_values,
            progress2=progress2_values,
            progress3=progress3_values
        )
    else:
        return render_template("progress.html", title="Tiến trình", progress=None)

@app.route("/getting-started", methods=("GET", "POST"), strict_slashes=False)
def getting_started():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    form = getting_started_form()

    if form.validate_on_submit():
        value1 = form.value1.data
        value2 = form.value2.data
        value3 = form.value3.data
        baseprogress = f"{value1};{value2};{value3}"

        user_id = session['user_id']

        existing_progress = Progress.query.filter_by(user_id=user_id).first()
        if existing_progress:
            existing_progress.baseprogress = baseprogress
            existing_progress.progress1 = baseprogress
            existing_progress.progress2 = ""
            existing_progress.progress3 = ""
        else:
            new_progress = Progress(
                user_id=user_id,
                baseprogress=baseprogress,
                progress1=baseprogress,
                progress2="",
                progress3=""
            )
            db.session.add(new_progress)

        db.session.commit()
        return redirect(url_for('progress'))

    return render_template("getting_started.html", form=form)
if __name__ == "__main__":
    app.run(debug=True)
