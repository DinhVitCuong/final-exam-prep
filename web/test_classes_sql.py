from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import random
import math
from models import Subject, QAs, Test, Progress, ProblemTypes
from app import db

def parse_rate_string(rate_string):
    # Split the string by underscores to separate each group
    groups = rate_string.split("_")
    # Split each group by hyphens and convert the values to integers
    parsed_rate = [list(map(int, group.split("-"))) for group in groups]
    return parsed_rate

# Query the database and convert the "rate" column
def get_rate_as_list(test_id):
    # Query the Test model to get the rate string for the given 
    test = Subject.query.filter_by(id=test_id).first()
    if test:
        rate_string = test.rate
        return parse_rate_string(rate_string)
    return None

class TestOrigin:
    def __init__(self, monhoc: str, chapter: int):
        self.monhoc = monhoc
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

    def select_questions(self, rate, num_questions, chapter=None):
        # Query the database for questions
        query = db.session.query(QAs)
        if chapter is not None:
            query = query.filter(
                QAs.id.like(f"{self.monhoc}%"),  # Filter by the subject character at the start
                QAs.id.like(f"_{str(chapter).zfill(2)}%")  # Filter by the two-digit chapter number
            )
        selected_questions = query.all()
        # print(selected_questions)
        # Separate questions by difficulty
        th_questions = [q for q in selected_questions if q.difficulty == 0]
        nb_questions = [q for q in selected_questions if q.difficulty == 1]
        vd_questions = [q for q in selected_questions if q.difficulty == 2]
        vdc_questions = [q for q in selected_questions if q.difficulty == 3]

        # Calculate the number of questions to select for each difficulty level
        th_percent, nb_percent, vd_percent, vdc_percent = rate
        num_th = int(num_questions * th_percent / 100)
        num_nb = int(num_questions * nb_percent / 100)
        num_vd = int(num_questions * vd_percent / 100)
        num_vdc = int(num_questions * vdc_percent / 100)
        
        # Randomly select questions for each difficulty level

        questions = (
            random.sample(th_questions, k=min(num_th, len(th_questions))) +
            random.sample(nb_questions, k=min(num_nb, len(nb_questions))) +
            random.sample(vd_questions, k=min(num_vd, len(vd_questions))) +
            random.sample(vdc_questions, k=min(num_vdc, len(vdc_questions)))
        )
        
        return questions
    def shuffle_questions(self, questions):
        th_questions = [q for q in questions if q.difficulty == 0]
        nb_questions = [q for q in questions if q.difficulty == 1]
        vd_questions = [q for q in questions if q.difficulty == 2]
        vdc_questions = [q for q in questions if q.difficulty == 3]
        
        random.shuffle(th_questions)
        random.shuffle(vd_questions)
        
        random.shuffle(vdc_questions)
        
        return th_questions + nb_questions + vd_questions + vdc_questions

class TestTotal(TestOrigin):
    def create_test(self, rate):
        questions = []
        if self.chapter <= 2:
            for i in range(1, self.chapter + 1):
                chapter_questions = self.select_questions(rate, 20, chapter=i)
                questions.extend(chapter_questions)

        
        else:
            for i in range(1, self.chapter + 1):
                chapter_questions = self.select_questions(rate, 10, chapter=i)
                questions.extend(chapter_questions)
        self.num_ques = len(questions)
        return questions

    def get_num_questions(self):
        return super().get_num_questions()


class TestChap(TestOrigin):
    def create_test(self,rate):
        questions = self.select_questions(rate, 30, self.chapter)
        self.num_ques = len(questions)
        return questions


# class pr_br_rcmd:
#     def __init__(self, subject_name, n_total=1, n_chap = 1):
#         self.subject_name = subject_name
#         self.n_total = n_total # so bai test tong
#         self.n_chap = n_chap # so bai test chuong 
#         self.top_t = []
#         self.top_c = []
#         self.chap_freq = {}
#         self.aim = 9
#         self.load_data()

#     def load_data(self):
#         try:
#             # Load total test results
#             total_results = db.session.query(Test).filter_by(test_type=1).order_by(Test.id.desc()).limit(self.n_total).all()
#             total_q = []
#             count_t = {}

#             if total_results:
#                 for result in total_results:
#                     wrong_answers = result.wrong_answer.split('_') if result.wrong_answer else []
#                     unchecked_answers = [
#                         result.questions.split('_')[i]
#                         for i, time in enumerate(result.time_result.split('_'))
#                         if time == '0'
#                     ] if result.time_result else []
                    
#                     for answer in wrong_answers + unchecked_answers:
#                         if answer[-1] != '4':  # Filter out certain answers
#                             total_q.append(answer)

#                 for answer in total_q:
#                     key = (answer[:5], answer[-1])
#                     chapter = answer[1:3]

#                     count_t[key] = count_t.get(key, 0) + 1
#                     self.chap_freq[chapter] = self.chap_freq.get(chapter, 0) + 1

#             self.top_t = sorted(count_t.items(), key=lambda x: x[1], reverse=True)[:5]
#             total_sum_all = sum(value for key, value in self.top_t)
#             self.top_t = [(key, math.ceil((value / total_sum_all) * 15)) for key, value in self.top_t]

#             # Load chapter test results
#             chapter_results = db.session.query(Test).filter_by(test_type=0).order_by(Test.id.desc()).limit(self.n_chap).all()
#             chap_q = []
#             count_c = {}

#             for result in chapter_results:
#                 wrong_answers = result.wrong_answer.split('_') if result.wrong_answer else []
#                 unchecked_answers = []  # Assuming unchecked answers aren't stored directly

#                 for answer in wrong_answers + unchecked_answers:
#                     if answer[-1] != '4':  # Filter out certain answers
#                         chap_q.append(answer)

#             for answer in chap_q:
#                 key = (answer[:5], answer[-1])
#                 chapter = answer[1:3]

#                 count_c[key] = count_c.get(key, 0) + 1
#                 self.chap_freq[chapter] = self.chap_freq.get(chapter, 0) + 1

#             self.top_c = sorted(count_c.items(), key=lambda x: x[1], reverse=True)[:3]
#             chapter_sum_all = sum(value for key, value in self.top_c)
#             self.top_c = [(key, math.ceil((value / chapter_sum_all) * 5)) for key, value in self.top_c]

#             # Sort chapter frequencies to find the top 2 chapters
#             self.chap_freq = sorted(self.chap_freq.items(), key=lambda x: x[1], reverse=True)[:2]
    
#         except Exception as e:
#             print(f"Error loading data: {str(e)}")
        
#     def containter_type(self, id):  # Return a list of questions for each id
#         return db.session.query(QAs).filter(QAs.id.like(f'{id[0][0]}%'), QAs.difficulty == id[0][1]).all()

#     def find_vdc(self, id_chap):  # Return a list of VDC questions
#         return db.session.query(QAs).filter_by(id=id_chap, difficulty=3).all()

#     def question_prep(self):  # Return a test with questions
#         QAs_list = []

#         for (id, _), num_id in self.top_t:
#             matching_questions = self.containter_type((id, _))
#             if len(matching_questions) >= num_id:
#                 QAs_list += random.sample(matching_questions, num_id)
#             else:
#                 QAs_list += matching_questions  # Add all if not enough to sample

#         for (id, _), num_id in self.top_c:
#             matching_questions = self.containter_type((id, _))
#             if len(matching_questions) >= num_id:
#                 QAs_list += random.sample(matching_questions, num_id)
#             else:
#                 QAs_list += matching_questions  # Add all if not enough to sample

#         # Adjust based on aim
#         if self.aim >= 9.5:
#             vdc_chap_1 = self.find_vdc(self.chap_freq[0][0])
#             vdc_chap_2 = self.find_vdc(self.chap_freq[1][0])

#             # Check if there are enough questions to sample
#             if len(vdc_chap_1) >= 2:
#                 QAs_list += random.sample(vdc_chap_1, 2)
#             else:
#                 QAs_list += vdc_chap_1  # Add all if not enough to sample

#             if len(vdc_chap_2) >= 1:
#                 QAs_list += random.sample(vdc_chap_2, 1)
#             else:
#                 QAs_list += vdc_chap_2  # Add all if not enough to sample

#         elif self.aim >= 9:
#             vdc_chap_1 = self.find_vdc(self.chap_freq[0][0])
#             vdc_chap_2 = self.find_vdc(self.chap_freq[1][0])

#             if len(vdc_chap_1) >= 1:
#                 QAs_list += random.sample(vdc_chap_1, 1)
#             else:
#                 QAs_list += vdc_chap_1  # Add all if not enough to sample

#             if len(vdc_chap_2) >= 1:
#                 QAs_list += random.sample(vdc_chap_2, 1)
#             else:
#                 QAs_list += vdc_chap_2  # Add all if not enough to sample

#         elif self.aim >= 8.5:
#             vdc_chap_1 = self.find_vdc(self.chap_freq[0][0])

#             if len(vdc_chap_1) >= 1:
#                 QAs_list += random.sample(vdc_chap_1, 1)
#             else:
#                 QAs_list += vdc_chap_1  # Add all if not enough to sample
        
#         if not QAs_list:
#             print("Warning: You haven't done any test.")

#         while len(QAs_list) < 25:
 
#             for (id, _), num_id in self.top_t:
#                 matching_questions = self.containter_type((id, _))
#                 if len(matching_questions) >= num_id:
#                     QAs_list += random.sample(matching_questions, num_id)

#         return QAs_list[:25] if QAs_list else []
    


# import random
# import torch
# from sentence_transformers import SentenceTransformer, util
# from sqlalchemy import func

# class pr_br_rcmd:
#     def __init__(self, subject_name, n_total=1, n_chap=1):
#         self.subject_name = subject_name
#         self.n_total = n_total
#         self.n_chap = n_chap
#         self.wrong_questions_ids = []
#         self.top_problem_types = []
#         self.mock_db = []
#         self.model = SentenceTransformer('multilingual-clip-ViT-B-32',token='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')
#         self.load_data()

#     def load_data(self):
#         try:
#             # Truy vấn kết quả tổng hợp từ cơ sở dữ liệu
#             total_results = db.session.query(Test).filter_by(test_type=1).order_by(Test.id.desc()).limit(self.n_total).all()
#             total_wrong_q = []

#             # Lấy danh sách ID của các câu trả lời sai từ kết quả tổng hợp
#             if total_results:
#                 for result in total_results:
#                     wrong_answers = result.wrong_answer.split('_') if result.wrong_answer else []
#                     unchecked_answers = [
#                         result.questions.split('_')[i]
#                         for i, time in enumerate(result.time_result.split('_'))
#                         if time == '0'
#                     ] if result.time_result else []

#                     total_wrong_q.extend(wrong_answers + unchecked_answers)

#                 self.wrong_questions_ids = total_wrong_q

#             # Truy vấn các câu hỏi từ ngân hàng câu hỏi
#             self.mock_db = db.session.query(QAs).filter(QAs.id.like(f'{self.subject_name}%')).all()
#             self.compute_similarity()

#         except Exception as e:
#             print(f"Cảnh báo: Có lỗi khi tải dữ liệu: {str(e)}")

#     def compute_similarity(self):
#         # Truy vấn các dạng bài từ cơ sở dữ liệu
#         problem_types = db.session.query(ProblemTypes.problem_types).filter(ProblemTypes.id_subject == self.subject_name).all()
#         problem_types = [ptype[0] for ptype in problem_types]  # Chuyển đổi tuple thành list

#         # Lấy nội dung của các câu hỏi sai
#         wrong_questions_texts = []
#         id_to_text = {qa.id: qa.question_text for qa in self.mock_db}
#         for q_id in self.wrong_questions_ids:
#             question_text = id_to_text.get(q_id, "")
#             if question_text:
#                 wrong_questions_texts.append(question_text)

#         # Kết hợp văn bản của các câu hỏi sai
#         combined_wrong_text = ' '.join(wrong_questions_texts)

#         # Mã hóa các dạng bài và câu hỏi sai bằng mô hình CLIP
#         problem_type_embeddings = self.model.encode(problem_types, convert_to_tensor=True)
#         wrong_question_embedding = self.model.encode(combined_wrong_text, convert_to_tensor=True)

#         # Tính độ tương đồng cosine giữa câu hỏi sai và các dạng bài
#         similarity_scores = util.cos_sim(wrong_question_embedding, problem_type_embeddings)[0]

#         # Lấy top 5 dạng bài
#         top_indices = torch.topk(similarity_scores, k=5).indices
#         self.top_problem_types = [problem_types[i] for i in top_indices]

#     def question_prep(self):
#         # Chuẩn bị câu hỏi từ top dạng bài
#         selected_questions = []

#         # Lấy văn bản của các câu hỏi trong ngân hàng câu hỏi
#         question_texts = [qa.question_text for qa in self.mock_db]

#         # Mã hóa các dạng bài và câu hỏi bằng mô hình CLIP
#         problem_type_embeddings = self.model.encode(self.top_problem_types, convert_to_tensor=True)
#         question_embeddings = self.model.encode(question_texts, convert_to_tensor=True)

#         # Tính độ tương đồng cosine giữa dạng bài và câu hỏi
#         similarity_matrix = util.cos_sim(problem_type_embeddings, question_embeddings)

#         # Chọn các câu hỏi có điểm similarity > 0.1
#         for idx in range(len(self.top_problem_types)):
#             scores = similarity_matrix[idx]
#             for q_idx, score in enumerate(scores):
#                 if score > 0.1:
#                     selected_questions.append((self.mock_db[q_idx], score.item()))

#         # Loại bỏ trùng lặp và sắp xếp theo điểm similarity
#         selected_questions = list({q[0].id: q for q in selected_questions}.values())
#         selected_questions.sort(key=lambda x: x[1], reverse=True)

#         # Tạo danh sách câu hỏi với các thuộc tính cần thiết
#         questions = []
#         for q_data, score in selected_questions:
#             question_obj = type('Question', (), {})()
#             question_obj.id = q_data.id
#             question_obj.image = q_data.image
#             question_obj.question = q_data.question_text
#             question_obj.options = q_data.options
#             question_obj.answer = q_data.answer
#             question_obj.explain = q_data.explanation
#             questions.append(question_obj)

#         return questions

import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

class pr_br_rcmd:
    def __init__(self, subject_name, n_total=1, n_chap=1):
        self.subject_name = subject_name
        self.n_total = n_total
        self.n_chap = n_chap
        self.wrong_questions_ids = []
        self.wrong_questions = []
        self.top_problem_types = []
        self.mock_db = []
        self.problem_types = []
        self.vectorizer = TfidfVectorizer()
        self.load_data()
        self.id_subject = str()

    def load_data(self):
        try:
            if self.subject_name == 'T':
                self.id_subject = 'S1'
            elif self.subject_name == 'L':
                self.id_subject = 'S2'
            elif self.subject_name == 'H':
                self.id_subject = 'S3'

            # Truy vấn kết quả tổng hợp từ cơ sở dữ liệu
            total_results = db.session.query(Test).filter_by(test_type=1).order_by(Test.id.desc()).limit(self.n_total).all()
            total_wrong_q = []

            # Lấy danh sách ID của các câu trả lời sai từ kết quả tổng hợp
            if total_results:
                for result in total_results:
                    wrong_answers = result.wrong_answer.split('_') if result.wrong_answer else []
                    unchecked_answers = [
                        result.questions.split('_')[i]
                        for i, time in enumerate(result.time_result.split('_'))
                        if time == '0'
                    ] if result.time_result else []
                    total_wrong_q.extend(wrong_answers + unchecked_answers)
                self.wrong_questions_ids = total_wrong_q

            # Truy vấn các câu hỏi từ ngân hàng câu hỏi có ID bắt đầu bằng subject_name
            self.mock_db = db.session.query(QAs).filter(QAs.id.like(f'{self.subject_name}%')).all()

            if self.wrong_questions_ids:
                questions = db.session.query(QAs.question).filter(QAs.id.in_(self.wrong_questions_ids)).all()
                self.wrong_questions = [q[0] for q in questions]

            problem_types = db.session.query(ProblemTypes.problem_types).filter(ProblemTypes.id_subject == self.id_subject).all()
            self.problem_types = [ptype[0] for ptype in problem_types]
            self.compute_similarity()

        except Exception as e:
            print(f"Cảnh báo: Có lỗi khi tải dữ liệu: {str(e)}")

    def compute_similarity(self):
        problem_type_counts = Counter()

        # Áp dụng TF-IDF cho tất cả các dạng bài và từng câu hỏi sai
        for wrong_question in self.wrong_questions:
            all_texts = self.problem_types + [wrong_question]
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)

            # Tính độ tương đồng cosine giữa câu hỏi sai và các dạng bài
            similarity_scores = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]

            # Tìm dạng bài có độ tương đồng cao nhất với câu hỏi sai hiện tại
            most_similar_index = similarity_scores.argmax()
            most_similar_problem_type = self.problem_types[most_similar_index]

            # Đếm số lần dạng bài tập xuất hiện nhiều nhất trong các câu hỏi sai
            problem_type_counts[most_similar_problem_type] += 1

        # Lấy top 5 dạng bài sai nhiều nhất
        self.top_problem_types = [ptype for ptype, _ in problem_type_counts.most_common(5)]
        print("Top 5 dạng bài sai nhiều nhất:", self.top_problem_types)


    def question_prep(self):
        # Chuẩn bị câu hỏi từ các dạng bài trong top problem types
        selected_questions = []

        # Lấy văn bản của các câu hỏi từ ngân hàng câu hỏi
        question_texts = [qa.question for qa in self.mock_db]

        # Kiểm tra nếu self.top_problem_types hoặc question_texts trống
        if not self.top_problem_types or not question_texts:
            print("Warning: No top problem types or question texts available for similarity calculation.")
            return selected_questions  # Trả về danh sách câu hỏi trống

        # Áp dụng TF-IDF cho cả dạng bài trong top_problem_types và câu hỏi trong mock_db
        all_texts = self.top_problem_types + question_texts
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        # Tính độ tương đồng cosine giữa dạng bài và câu hỏi
        similarity_matrix = cosine_similarity(
            tfidf_matrix[:len(self.top_problem_types)], 
            tfidf_matrix[len(self.top_problem_types):]
        )

        # Lấy câu hỏi có độ tương đồng cao với top problem types
        for idx, scores in enumerate(similarity_matrix):
            for q_idx, score in enumerate(scores):
                if score > 0.5:  # Ngưỡng điểm similarity
                    selected_questions.append(self.mock_db[q_idx])

        # Loại bỏ trùng lặp dựa trên ID câu hỏi
        unique_questions = list({q.id: q for q in selected_questions}.values())

        # Lấy ngẫu nhiên 30 câu hỏi từ danh sách đã lọc
        random_questions = random.sample(unique_questions, min(len(unique_questions), 30))

        # Tạo danh sách câu hỏi với các thuộc tính cần thiết
        questions = []
        for q_data in random_questions:
            question_obj = type('Question', (), {})()
            question_obj.id = q_data.id
            question_obj.image = q_data.image
            question_obj.question = q_data.question
            question_obj.options = q_data.options
            question_obj.answer = q_data.answer
            question_obj.explain = q_data.explain
            questions.append(question_obj)

        return questions




    
# import json
# import random
# import torch
# from sentence_transformers import SentenceTransformer, util

# class pr_br_rcmd:
#     def __init__(self, subject_name, n_total=1, n_chap=1):
#         self.subject_name = subject_name
#         self.n_total = n_total
#         self.n_chap = n_chap
#         self.wrong_questions_ids = []
#         self.top_problem_types = []
#         self.mock_db = []
#         self.model = SentenceTransformer('multilingual-clip-ViT-B-32')  
#         self.load_data()

#     def load_data(self):
#         try:
#             # Tải kết quả tổng
#             with open(f'{self.subject_name}_total_results.json', 'r', encoding='utf-8') as f:
#                 data = json.load(f)[-self.n_total:]
#                 total_wrong_q = []

#                 # Lấy danh sách ID của các câu trả lời sai
#                 for result in data:
#                     if result["wrong_answers"]:
#                         total_wrong_q.extend(result["wrong_answers"])
#                     if result["unchecked_answers"]:
#                         total_wrong_q.extend(result["unchecked_answers"])

#                 self.wrong_questions_ids = total_wrong_q

#             # Tải dữ liệu câu hỏi
#             with open(f"{self.subject_name}_mock.json", 'r', encoding='utf-8') as file:
#                 mock_db_data = json.load(file)
#                 self.mock_db = mock_db_data["QAs"]

#             # Gọi hàm tính similarity
#             self.compute_similarity()

#         except FileNotFoundError as e:
#             print(f"Cảnh báo: File không tồn tại: {str(e)}")
#             return None

#     def compute_similarity(self):
#         # Tải các dạng bài
#         with open(f'{self.subject_name}_types.json', 'r', encoding='utf-8') as f:
#             types_data = json.load(f)
#             problem_types = types_data["problem_type"]

#         # Lấy nội dung của các câu hỏi sai
#         wrong_questions_texts = []
#         id_to_text = {qa["ID"]: qa["question_text"] for qa in self.mock_db}
#         for q_id in self.wrong_questions_ids:
#             question_text = id_to_text.get(q_id, "")
#             wrong_questions_texts.append(question_text)

#         # Kết hợp văn bản của các câu hỏi sai
#         combined_wrong_text = ' '.join(wrong_questions_texts)

#         # Mã hóa các dạng bài và câu hỏi sai bằng mô hình CLIP
#         problem_type_embeddings = self.model.encode(problem_types, convert_to_tensor=True)
#         wrong_question_embedding = self.model.encode(combined_wrong_text, convert_to_tensor=True)

#         # Tính độ tương đồng cosine giữa câu hỏi sai và các dạng bài
#         similarity_scores = util.cos_sim(wrong_question_embedding, problem_type_embeddings)[0]

#         # Lấy top 5 dạng bài
#         top_indices = torch.topk(similarity_scores, k=5).indices
#         self.top_problem_types = [problem_types[i] for i in top_indices]

#     def question_prep(self):
#         # Từ top dạng bài, chọn các câu hỏi tương ứng
#         selected_questions = []

#         # Lấy văn bản của các câu hỏi trong ngân hàng đề
#         question_texts = [qa["question_text"] for qa in self.mock_db]

#         # Mã hóa các dạng bài và câu hỏi bằng mô hình CLIP
#         problem_type_embeddings = self.model.encode(self.top_problem_types, convert_to_tensor=True)
#         question_embeddings = self.model.encode(question_texts, convert_to_tensor=True)

#         # Tính độ tương đồng cosine giữa dạng bài và câu hỏi
#         similarity_matrix = util.cos_sim(problem_type_embeddings, question_embeddings)

#         # Chọn các câu hỏi có điểm similarity > 0.1
#         for idx in range(len(self.top_problem_types)):
#             scores = similarity_matrix[idx]
#             for q_idx, score in enumerate(scores):
#                 if score > 0.1:
#                     selected_questions.append((self.mock_db[q_idx], score.item()))

#         # Loại bỏ trùng lặp và sắp xếp theo điểm similarity
#         selected_questions = list({q[0]['ID']: q for q in selected_questions}.values())
#         selected_questions.sort(key=lambda x: x[1], reverse=True)

#         # Tạo danh sách câu hỏi với các thuộc tính cần thiết
#         questions = []
#         for q_data, score in selected_questions:
#             question_obj = type('Question', (), {})()
#             question_obj.id = q_data['ID']
#             question_obj.image = q_data.get('image', '')
#             question_obj.question = q_data['question_text']
#             question_obj.options = q_data['options']
#             question_obj.answer = q_data['answer']
#             question_obj.explain = q_data.get('explanation', '')
#             questions.append(question_obj)

#         return questions
