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
    SelectField
)

from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, EqualTo, Email, Regexp ,Optional, NumberRange
import email_validator
from flask_login import current_user
from wtforms import ValidationError,validators
from models import User


class login_form(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    pwd = PasswordField(validators=[InputRequired(), Length(min=8, max=72)])
    # Placeholder labels to enable form rendering
    username = StringField(
        validators=[Optional()]
    )


class register_form(FlaskForm):
    username = StringField(
        validators=[
            InputRequired(),
            Length(3, 20, message="Please provide a valid name"),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, " "numbers, dots or underscores",
            ),
        ]
    )
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    pwd = PasswordField(validators=[InputRequired(), Length(8, 72)])
    cpwd = PasswordField(
        validators=[
            InputRequired(),
            Length(8, 72),
            EqualTo("pwd", message="Passwords must match !"),
        ]
    )


    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered!")

    def validate_uname(self, uname):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username already taken!")
    
class getting_started_form(FlaskForm):
    value1 = DecimalField(
        'Value 1',
        validators=[InputRequired(), NumberRange(min=0, max=10, message='Hãy nói đúng sự thật nào! bạn có ấn nhầm số không')]
    )
    value2 = DecimalField(
        'Value 2',
        validators=[InputRequired(), NumberRange(min=0, max=10, message='Hãy nói đúng sự thật nào! bạn có ấn nhầm số không')]
    )
    value3 = DecimalField(
        'Value 3',
        validators=[InputRequired(), NumberRange(min=0, max=10, message='Hãy nói đúng sự thật nào! bạn có ấn nhầm số không')]
    )
    submit = SubmitField('Submit')

class test_selection_form(FlaskForm):
    subject = SelectField('Subject', choices=[], validators=[InputRequired()])
    test_type = RadioField('Test Type', choices=[('total', 'Total Test'), ('chapter', 'Chapter Test')], validators=[InputRequired()])
    total_chapters = SelectMultipleField('Select Chapters for Total Test', choices=[], coerce=str)
    chapter = SelectField('Select a Chapter for Chapter Test', choices=[], validators=[InputRequired()])
    submit = SubmitField('Start Test')

class select_univesity_form(FlaskForm):
    budget = StringField('Budget lower than', validators=[InputRequired(), NumberRange(min=0)])
    location = SelectMultipleField('Location', choices=[('us', 'United States'), ('uk', 'United Kingdom'), ('eu', 'Europe'), ('asia', 'Asia')])
    major = SelectMultipleField('Subject Category', choices=[('engineering', 'Engineering'), ('arts', 'Arts'), ('science', 'Science'), ('business', 'Business')])
    subject_category = SelectField('Major', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[InputRequired()])
    university = SelectField('University', choices=[])
    check = SubmitField('Check')
    submit = SubmitField('Submit')