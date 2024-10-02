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
import os
import json
from app import create_app, db, login_manager, bcrypt
from models import User, Progress, Test, Universities, QAs, Subject, SubjectCategory
import random
from test_classes_sql import TestOrigin, TestTotal, TestChap
from datetime import datetime

app = create_app()

# Create a test record from QAs objects
def create_test_record(qa_list, knowledge, type):
    question_ids = [qa.id for qa in qa_list]
    questions = "_".join(question_ids)
    
    wrong_percentage = random.randint(10, 50)
    num_wrong_answers = int(len(question_ids) * (wrong_percentage / 100))
    wrong_answers = random.sample(question_ids, k=num_wrong_answers)
    wrong_answer = "_".join(wrong_answers)
    
    result = "_".join('0' if q in wrong_answers else '1' for q in question_ids)
    time_result = "_".join(str(random.randint(5, 60)) for _ in question_ids)
    
    test_record = {
        "user_id": 1,  # Assuming a specific user ID for the example
        "test_type": type, # ,random.choice([0, 1, 3]),
        "time": datetime.now().strftime('%Y-%m-%d'),
        "knowledge": knowledge,
        "questions": questions,
        "wrong_answer": wrong_answer,
        "result": result,
        "time_result": time_result
    }
    
    return test_record

with app.app_context():
    rate = [40, 20, 30, 10]
    
    # Create multiple test records and push them to the database
    for i in range(1, 15):
        if i > 7:
            j = i % 7 + 1
        else:
            j = i
        test_total = TestChap("L", j)
        questions_total = test_total.create_test(rate)
        test_data = create_test_record(questions_total, str(j).zfill(2) , 0)
        
        new_test_record = Test(
            user_id=test_data['user_id'],
            test_type=test_data['test_type'],
            time=datetime.strptime(test_data['time'], '%Y-%m-%d').date(),
            knowledge=test_data['knowledge'],
            questions=test_data['questions'],
            wrong_answer=test_data['wrong_answer'],
            result=test_data['result'],
            time_result=test_data['time_result']
        )
        
        db.session.add(new_test_record)
        print(f"Test record added to session: {new_test_record}")
    db.session.commit()