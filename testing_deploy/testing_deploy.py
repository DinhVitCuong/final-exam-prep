import json
import random
import webbrowser
from flask import Flask, request, render_template_string, g
from testing_classes import TestTotal,TestChap
app = Flask(__name__)


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
        
        # Generate HTML file
        self.generate_html(questions)
        self.num_ques = len(questions)
        return questions

    def generate_html(self, questions):
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Multiple Choice Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .question { margin-bottom: 20px; }
                .options { list-style-type: none; padding: 0; }
                .options li { margin: 5px 0; }
                .timer { font-size: 20px; color: red; margin-bottom: 20px; }
            </style>
            <script>
                // Timer countdown function
                function startTimer(duration, display) {
                    var timer = duration, minutes, seconds;
                    var countdown = setInterval(function () {
                        minutes = parseInt(timer / 60, 10);
                        seconds = parseInt(timer % 60, 10);

                        minutes = minutes < 10 ? "0" + minutes : minutes;
                        seconds = seconds < 10 ? "0" + seconds : seconds;

                        display.textContent = minutes + ":" + seconds;

                        if (--timer < 0) {
                            clearInterval(countdown);
                            document.getElementById("testForm").submit();
                        }
                    }, 1000);
                }

                window.onload = function () {
                    var fiveMinutes = 60 * 5,
                        display = document.querySelector('#time');
                    startTimer(fiveMinutes, display);
                };
            </script>
        </head>
        <body>
            <h1>Multiple Choice Test</h1>
            <div class="timer">Time left: <span id="time">05:00</span></div>
            <form id="testForm" action="/submit" method="post">
        """

        for qa in questions:
            html_content += f"""
            <div class="question">
                <p>{qa["question"]}</p>
                <ul class="options">
            """
            for option in qa["options"]:
                html_content += f"""
                    <li>
                        <label>
                            <input type="radio" name="{qa["ID"]}" value="{option}">
                            {option}
                        </label>
                    </li>
                """
            html_content += """
                </ul>
            </div>
            """

        html_content += """
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
        """

        with open("templates/test.html", "w") as file:
            file.write(html_content)

    def check_correct_answers(self, user_answers):
        with open(f'{self.subject_name}_test.json', 'r') as f:
            questions = json.load(f)
        
        correct_answers = {qa['ID']: qa['answer'] for qa in questions}
        score = 0
        wrong_answers = []

        for qa_id, user_answer in user_answers.items():
            if user_answer.split()[-1] == correct_answers[qa_id]:
                score += 1
            else:
                wrong_answers.append(qa_id)
        self.save_test_result(score, wrong_answers)
        return score, wrong_answers

    def generate_results_html(self, score, wrong_answers):
        results_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .results {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h1>Test Results</h1>
            <div class="results">
                <p>Score: {score}/{self.num_ques}</p>
                <p>Wrong Answers: {', '.join(wrong_answers)}</p>
            </div>
        </body>
        </html>
        """
        with open("templates/results.html", "w") as file:
            file.write(results_html)
    
    def save_test_result(self, score, wrong_answers):
        if self.test_type == 'total':
            result = {
                'score': score,
                'wrong_answers': wrong_answers
            }
            filename = f'{self.subject_name}_total_results.json'
        else:
            result = {
                'score': score,
                'wrong_answers': wrong_answers,
                'chapter' : self.num_chapters
            }
            filename = f'{self.subject_name}_chapter_results.json'

        try:
            with open(filename, 'r') as f:
                results = json.load(f)
        except FileNotFoundError:
            results = []

        results.append(result)

        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
            

# Flask routes to handle the test and submission
@app.route('/test')
def test():
    return render_template_string(open('templates/test.html').read())

@app.route('/submit', methods=['POST'])
def submit():
    user_answers = request.form.to_dict()
    
    # Print out the user answers
    print("User Answers:", user_answers)
    
    score, wrong_answers = deploy.check_correct_answers(user_answers)
    deploy.generate_results_html(score, wrong_answers)
    return render_template_string(open('templates/results.html').read())

@app.before_request
def before_request():
    g.deploy = deploy


if __name__ == '__main__':
    deploy = TestingDeploy(threshold=[60, 30, 10], test_type="chapter", subject_name="T",num_chapters = 3)
    deploy.create_test()
    app.run(debug=True)
    webbrowser.open('http://localhost:5000/test')

