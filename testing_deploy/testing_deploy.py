import json
import webbrowser
from flask import Flask, request, render_template, session, redirect, url_for, g
from testing_classes import TestTotal, TestChap

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary to use sessions


class TestingDeploy:
    def __init__(self, threshold, test_type, subject_name, num_chapters=0):
        self.threshold = threshold
        self.test_type = test_type
        self.subject_name = subject_name
        self.num_chapters = num_chapters
        self.result = None
        self.num_ques = None

    def create_test_total(self, num_chapters):
        test_total = TestTotal(self.subject_name)
        questions = test_total.create_test(num_chapters)
        return questions

    def create_test_chapter(self, chapter):
        test_chap = TestChap(self.subject_name, chapter)
        questions = test_chap.create_test()
        return questions

    def create_test(self):
        if self.test_type == "total":
            questions = self.create_test_total(self.num_chapters)
        elif self.test_type == "chapter":
            questions = self.create_test_chapter(self.num_chapters)

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
        result = {
                'score': score,
                'right_answers': right_answers,
                'wrong_answers': wrong_answers,
                'unchecked_answers': unchecked_answers,
                'chapter': self.num_chapters,
                'time_spent_per_question': time_spent_per_question,
                'total_questions': self.num_ques
            }
        if self.test_type == 'total':
            filename = f'{self.subject_name}_total_results.json'
        else:
            filename = f'{self.subject_name}_chapter_results.json'

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
    # Load questions from your JSON file or database
    with open(f'{session["subject_name"]}_test.json', 'r') as f:
        questions = json.load(f)

    # Get the current question based on the question_number
    current_question = questions[question_number - 1]

    # If the questions object contains non-serializable data, clean it
    questions_serializable = jsonify(questions).json

    return render_template('question.html', question=current_question, question_number=question_number, total_questions=len(questions), questions=questions_serializable)



@app.route('/submit', methods=['POST', 'GET'])
def submit():
    # Get all answers from the session
    selections = json.loads(request.form['selections'])
    print(selections)
    score, wrong_answers = deploy.check_correct_answers(selections)

    return render_template('results.html', score=score, wrong_answers=wrong_answers, total=deploy.num_ques)


@app.before_request
def before_request():
    g.deploy = deploy

# chu thich
# doi voi test tong neu num_chapters <= 2 thi lay 15 cau moi chapter, neu num_chapters > 2 thi lay 10 cau moi chapter

if __name__ == '__main__':
    deploy = TestingDeploy(threshold=[60, 30, 10], test_type="total", subject_name="T", num_chapters=3)
    deploy.create_test()
    app.run(debug=True)
    webbrowser.open('http://localhost:5000/')
