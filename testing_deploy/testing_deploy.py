import json
import webbrowser
from flask import Flask, request, render_template, session, redirect, url_for, g
from testing_classes import TestTotal, TestChap
from pr_br_rcmd import pr_br_rcmd
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary to use sessions


class TestingDeploy:
    def __init__(self, threshold, test_type, subject_name, num_chapters=0, rate=None):
        self.threshold = threshold
        self.test_type = test_type if test_type in ['total', 'chapter', 'practice'] else None # left a warning
        self.subject_name = subject_name
        self.num_chapters = num_chapters
        self.result = None
        self.num_ques = None
        self.rate = rate
        self.time_limit = 90 if self.test_type == 'total' else 45

    def create_test_total(self, num_chapters):
        test_total = TestTotal(self.subject_name, self.rate, self.num_chapters)
        questions = test_total.create_test()
        return questions

    def create_test_chapter(self, chapter):
        test_chap = TestChap(self.subject_name, self.rate, self.num_chapters)
        questions = test_chap.create_test()
        return questions
    def create_test_practice(self):
        test_practice = pr_br_rcmd(self.subject_name, 5, 1)
        questions = test_practice.question_prep()
        return questions

    def create_test(self):
        if self.test_type == "total":
            questions = self.create_test_total(self.num_chapters)
        elif self.test_type == "chapter":
            questions = self.create_test_chapter(self.num_chapters)
        else:
            questions = self.create_test_practice()
        # Save questions to JSON file
        with open(f'{self.subject_name}_test.json', 'w') as f:
            json.dump(questions, f)

        # Store the number of questions for use in scoring
        self.num_ques = len(questions)
        return questions

    def check_correct_answers(self, user_answers):
        with open(f'{self.subject_name}_test.json', 'r') as f:
            questions = json.load(f)

        correct_answers = {qa['ID']: qa['answer'] for qa in questions}
        score = 0
        wrong_answers = []
        time_spent_per_question = {}
        right_answers = []
        for qa_id, user_data in user_answers.items():
            user_answer = user_data.get('selectedOption')
            time_spent = user_data.get('timeSpent', 0)  # Default to 0 if not provided
            if user_answer is None:
                continue
            print(user_answer.split())
            print(correct_answers[qa_id])

            # Save time spent on the question
            time_spent_per_question[qa_id] = time_spent

            # Check if the answer is correct
            if user_answer.split()[1] == correct_answers[qa_id]:
                score += 1
                right_answers.append(qa_id)
            else:
                wrong_answers.append(qa_id)
            ## remove qa_id from correct_answers
            del correct_answers[qa_id]
        unchecked_answers = list(correct_answers.keys())
        self.save_test_result(score,right_answers, wrong_answers, unchecked_answers, time_spent_per_question)
        return score, wrong_answers

    def save_test_result(self, score, right_answers, wrong_answers,unchecked_answers, time_spent_per_question):
        completion_time = datetime.now().strftime("%Y-%m-%d")
        result = {
                'score': score,
                'right_answers': right_answers,
                'wrong_answers': wrong_answers,
                'unchecked_answers': unchecked_answers,
                'chapter': self.num_chapters,
                'time_spent_per_question': time_spent_per_question,
                'total_questions': self.num_ques,
                'completion_time': completion_time
            }
        
        filename = f'{self.subject_name}_{self.test_type}_results.json'

        try:
            with open(filename, 'r') as f:
                results = json.load(f)
        except FileNotFoundError:
            results = []

        results.append(result)

        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)


@app.route('/')
def index():
    # Start the quiz by setting the subject name and redirecting to the first question
    session['subject_name'] = 'T'
    return redirect(url_for('question', question_number=1))
 

from flask import jsonify

@app.route('/question/<int:question_number>', methods=['GET', 'POST'])
def question(question_number):
    with open(f'{session["subject_name"]}_test.json', 'r') as f:
        questions = json.load(f)

    current_question = questions[question_number - 1]
    questions_serializable = jsonify(questions).json

    return render_template(
        'question.html', 
        question=current_question, 
        question_number=question_number, 
        total_questions=len(questions), 
        questions=questions_serializable,
        time_limit=deploy.time_limit  # Pass the time limit to the template
    )



@app.route('/submit', methods=['POST', 'GET'])
def submit():
    # Check if 'selections' is in the form data
    if 'selections' not in request.form:
        # Handle the case where no selections were submitted (e.g., time expired)
        print("No selections were made. Time might have expired.")
        selections = {}
    else:
        # Get all answers from the form data
        selections = json.loads(request.form['selections'])

    print(selections)
    
    # If selections is empty, you may want to handle it differently
    if not selections:
        score = 0
        wrong_answers = []
    else:
        score, wrong_answers = deploy.check_correct_answers(selections)
    
    return render_template('results.html', score=score, wrong_answers=wrong_answers, total=deploy.num_ques)


@app.before_request
def before_request():
    g.deploy = deploy

# chu thich
# doi voi test tong neu num_chapters <= 2 thi lay 15 cau moi chapter, neu num_chapters > 2 thi lay 10 cau moi chapter

if __name__ == '__main__':
    rate = [40, 20, 30 ,10]
    deploy = TestingDeploy(threshold=[60, 30, 10], test_type="total", subject_name="T", num_chapters=3, rate=rate)
    deploy.create_test()
    app.run(debug=True)
    webbrowser.open('http://localhost:5000/')
