import json
import random
import math


class TestOrigin:
    def __init__(self, monhoc: str, rate : list,chapter: int):
        self.monhoc = monhoc
        self.rate = rate
        self.num_ques = None
        self.timelimit = None   
        self.chapter = chapter
    def create_test(self):
        pass

    def is_test_total(self):
        pass

    def is_test_chap(self):
        pass
    def get_num_questions(self):
        return self.num_ques
    def select_questions(self, num_questions, chapter=None):
        with open(f"{self.monhoc}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        
        selected_questions = []
        for question in mock_db:
            if chapter is None or question["ID"][1:3] == str(chapter).zfill(2):
                selected_questions.append(question)
            
        th_percent, nb_percent, vd_percent, vdc_percent = self.rate

        th_questions = [q for q in selected_questions if q["difficulty"] == 1]
        nb_questions = [q for q in selected_questions if q["difficulty"] == 2]
        vd_questions = [q for q in selected_questions if q["difficulty"] == 3]
        vdc_questions = [q for q in selected_questions if q["difficulty"] == 4]
        
        num_th = int(num_questions * th_percent / 100)
        num_nb = int(num_questions * nb_percent / 100)
        num_vd = int(num_questions * vd_percent / 100)
        num_vdc = int(num_questions * vdc_percent / 100)
        
        questions = random.sample(th_questions, num_th) + random.sample(nb_questions, num_nb) + random.sample(vd_questions, num_vd) + random.sample(vdc_questions, num_vdc)
        
        return questions
    
    def shuffle_questions(self, questions):
        th_questions = [q for q in questions if q["difficulty"] == 1]
        nb_questions = [q for q in questions if q["difficulty"] == 2]
        vd_questions = [q for q in questions if q["difficulty"] == 3]
        vdc_questions = [q for q in questions if q["difficulty"] == 4]
        
        random.shuffle(th_questions)
        random.shuffle(vd_questions)
        
        random.shuffle(vdc_questions)
        
        return th_questions + nb_questions + vd_questions + vdc_questions


class TestTotal(TestOrigin):

    def create_test(self):
        questions = []
        if self.chapter <= 2:
            for i in range(1, self.chapter + 1):
                chapter_questions = self.select_questions(15, chapter=i)
                questions.extend(chapter_questions)

            questions = self.shuffle_questions(questions)
        else:
            for i in range(1, self.chapter + 1):
                chapter_questions = self.select_questions(10, chapter=i)
                questions.extend(chapter_questions)

            questions = self.shuffle_questions(questions)
        self.num_ques = len(questions)
        return questions

    
    def get_num_questions(self):
        return super().get_num_questions()


class TestChap(TestOrigin):

    def create_test(self):
        questions = self.select_questions(30, self.chapter)
        questions = self.shuffle_questions(questions)
        self.num_ques = len(questions)
        return questions
    
    def is_theory(self):
        return self.select_questions(30, 80, 15, 5)

    def is_practice(self):
        return self.select_questions(30, 40, 40, 20)

    

# Example usage
# "T" is the subject code for "Toan"
rate = [40,20,30,10]
test_total = TestTotal("T",rate, 3)
questions_total = test_total.create_test() # 3 là số chương đã học
print("Total Test Questions:", questions_total)

test_chap = TestChap("T", rate, 3)
questions_chap = test_chap.create_test()
print("Chapter Test Questions:", questions_chap)



class pr_br_rcmd:
    def __init__(self, subject_name, n_total=1, n_chap=1):
        self.subject_name = subject_name
        self.n_total = n_total
        self.n_chap = n_chap
        self.top_t = []
        self.top_c = []
        self.chap_freq = {}
        self.aim = 9
        self.load_data()

    def load_data(self):
        try:
            # Load total results
            with open(f'{self.subject_name}_total_results.json', 'r') as f:
                data = json.load(f)[-self.n_total:]
                total_q = []
                count_t = {}

                # Process total results
                for i in range(self.n_total):
                    if data[i]["wrong_answers"] and data[i]["wrong_answers"][-1][-1] != '4':
                        total_q += data[i]["wrong_answers"]
                    if data[i]["unchecked_answers"] and data[i]["unchecked_answers"][-1][-1] != '4':
                        total_q += data[i]["unchecked_answers"]

                for i in total_q:
                    key = (i[:5], i[-1])
                    chapter = i[1:3]

                    if key in count_t:
                        count_t[key] += 1
                    else:
                        count_t[key] = 1

                    if chapter in self.chap_freq:
                        self.chap_freq[chapter] += 1
                    else:
                        self.chap_freq[chapter] = 1

                if len(count_t) >= 5:
                    self.top_t = sorted(count_t.items(), key=lambda x: x[1], reverse=True)[:5]
                else:
                    self.top_t = sorted(count_t.items(), key=lambda x: x[1], reverse=True)

                total_sum_all = sum(value for key, value in self.top_t)
                self.top_t = [(key, math.ceil((value / total_sum_all) * 15)) for key, value in self.top_t]

            # Load chapter results
            with open(f'{self.subject_name}_chapter_results.json', 'r') as f:
                data = json.load(f)[-self.n_chap:]
                chap_q = []
                count_c = {}

                # Process chapter results
                for i in range(self.n_chap):
                    if data[i]["wrong_answers"] and data[i]["wrong_answers"][-1][-1] != '4':
                        chap_q += data[i]["wrong_answers"]
                    if data[i]["unchecked_answers"] and data[i]["unchecked_answers"][-1][-1] != '4':
                        chap_q += data[i]["unchecked_answers"]

                for i in chap_q:
                    key = (i[:5], i[-1])
                    chapter = i[1:3]

                    if key in count_c:
                        count_c[key] += 1
                    else:
                        count_c[key] = 1

                    if chapter in self.chap_freq:
                        self.chap_freq[chapter] += 1
                    else:
                        self.chap_freq[chapter] = 1

                if len(count_c) >= 3:
                    self.top_c = sorted(count_c.items(), key=lambda x: x[1], reverse=True)[:3]
                else:
                    self.top_c = sorted(count_c.items(), key=lambda x: x[1], reverse=True)

                chapter_sum_all = sum(value for key, value in self.top_c)
                self.top_c = [(key, math.ceil((value / chapter_sum_all) * 5)) for key, value in self.top_c]

            # Sort chapter frequencies to find the top 2 chapters
            self.chap_freq = sorted(self.chap_freq.items(), key=lambda x: x[1], reverse=True)[:2]

        except FileNotFoundError as e:
            print(f"Warning: The file was not found: {str(e)}")
            return None

    def containter_type(self, id):  # Return a list of questions for each id
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]

        return [qa for qa in mock_db if qa["ID"][:5] == id[0][0] and qa["ID"][-1] == id[0][1]]
    def find_vdc(self,id_chap):  # Return a list of VDC questions
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]
        return [qa for qa in mock_db if qa["ID"][1:3] == id_chap and qa["difficulty"] == 4]
    def question_prep(self):  # Return a test with questions
        QAs = []
        with open(f"{self.subject_name}_mock.json", 'r') as file:
            mock_db = json.load(file)["QAs"]

        for (id, _), num_id in self.top_t:
            matching_questions = [qa for qa in mock_db if qa["ID"][:5] == id]
            if len(matching_questions) >= num_id:
                QAs += random.sample(matching_questions, num_id)
            else:
                QAs += matching_questions  # Add all if not enough to sample

        for (id, _), num_id in self.top_c:
            matching_questions = [qa for qa in mock_db if qa["ID"][:5] == id]
            if len(matching_questions) >= num_id:
                QAs += random.sample(matching_questions, num_id)
            else:
                QAs += matching_questions  # Add all if not enough to sample

        # Adjust based on aim
        if self.aim >= 8.5 and self.aim < 9:
            # Insert logic to add VDC questions based on the top chapters in self.chap_freq
            # 1 vdc
            QAs += random.sample(self.find_vdc(self.chap_freq[0][0]), 1)
        elif self.aim >= 9 and self.aim < 9.5:
            # 2 vdc
            QAs += random.sample(self.find_vdc(self.chap_freq[0][0]), 1)
            QAs += random.sample(self.find_vdc(self.chap_freq[1][0]), 1)
        elif self.aim >= 9.5:
            # 3 vdc
            QAs += random.sample(self.find_vdc(self.chap_freq[0][0]), 2)
            QAs += random.sample(self.find_vdc(self.chap_freq[1][0]), 1)
        else:
            pass
        return QAs