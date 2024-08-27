from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    IntegerField,
    DateField,
    TextAreaField,
    DecimalField,
    SubmitField,
    RadioField, 
    SelectMultipleField, 
    SelectField,
    HiddenField
)

from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, EqualTo, Email, Regexp ,Optional, NumberRange
from models import User, Progress, Test, Universities, QAs, Subject
import email_validator
from flask_login import current_user
from wtforms import ValidationError,validators
from models import User


class login_form(FlaskForm):
    identifier = StringField('Username or Email', validators=[InputRequired()])
    pwd = PasswordField(validators=[InputRequired(), Length(min=8, max=72)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class register_form(FlaskForm):
    username = StringField(
        validators=[
            InputRequired(),
            Length(3, 30, message="Please provide a valid name"),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, " "numbers, dots or underscores",
            ),
        ]
    )
    name = StringField(validators=[InputRequired()])
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    pwd = PasswordField(validators=[InputRequired(), Length(8, 72)])
    cpwd = PasswordField(
        validators=[
            InputRequired(),
            Length(8, 72),
            EqualTo("pwd", message="Passwords must match !"),
        ]
    )
    submit = SubmitField('Sign up')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered!")

    def validate_uname(self, uname):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username already taken!")
    
# class getting_started_form(FlaskForm):
#     value1 = DecimalField(
#         'Value 1',
#         validators=[InputRequired(), NumberRange(min=0, max=10, message='Hãy nói đúng sự thật nào! bạn có ấn nhầm số không')]
#     )
#     value2 = DecimalField(
#         'Value 2',
#         validators=[InputRequired(), NumberRange(min=0, max=10, message='Hãy nói đúng sự thật nào! bạn có ấn nhầm số không')]
#     )
#     value3 = DecimalField(
#         'Value 3',
#         validators=[InputRequired(), NumberRange(min=0, max=10, message='Hãy nói đúng sự thật nào! bạn có ấn nhầm số không')]
#     )
#     submit = SubmitField('Submit')

class select_univesity_form(FlaskForm):
    subject_category = SelectField('Subject Category', choices=[], validators=[InputRequired()])
    location = SelectField('Location', choices=[(None, 'Không rõ'), ('Hà Nội', 'Hà Nội'), ('Đà Nẵng', 'Đà Nẵng'), ('Hồ Chí Minh', 'Hồ Chí Minh')]
                           ,validators=[Optional()]
                           ,default=None)
    major = SelectField('Major', choices=[],validators=[Optional()])
    budget = StringField('Budget lower than',validators=[Optional()])
    university = SelectField('University', choices=[],validators=[Optional()])
    current_slide = StringField('Current Slide',validators=[Optional()],default=0)
    submit = SubmitField('Submit')
    
    def get_unique_subject_categories(self):
        # Query all subject categories
        categories = Universities.query.with_entities(Universities.subject_category).all()
        unique_categories = set()
        
        # Split and collect unique categories
        for category_string in categories:
            category_list = category_string[0].split(';')  # Split on semicolons
            unique_categories.update(category_list)
        
        # Return sorted list of unique categories as choices
        return [(category.strip(), category.strip()) for category in sorted(unique_categories)]

    def __init__(self, *args, **kwargs):
        super(select_univesity_form, self).__init__(*args, **kwargs)
        
        # Populate subject categories from the database
        self.subject_category.choices = self.get_unique_subject_categories()

class test_selection_form(FlaskForm):
    subject = SelectField('Subject', choices=[], validators=[InputRequired()])
    test_type = RadioField('Test Type', choices=[('total', 'Total Test'), ('chapter', 'Chapter Test')], validators=[InputRequired()])
    total_chapters = SelectMultipleField('Select Chapters for Total Test', choices=[], coerce=str)
    chapter = SelectField('Select a Chapter for Chapter Test', choices=[], validators=[InputRequired()])
    submit = SubmitField('Start Test')

class QuizForm(FlaskForm):
    timeSpent = HiddenField('Time Spent', validators=[InputRequired()])
    answers = HiddenField('Answers', validators=[InputRequired()])