from models import Subject, QAs, Test, Progress, ProblemTypes,LessonInfo
from app import db,create_app
import json
from sqlalchemy.orm import aliased
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

app = create_app()

with open(r'D:\Code\Python\projects\BangA\hehe\data_json\che_de2024.json','r',encoding='utf-8') as f:
    H = json.load(f)
with open(r'D:\Code\Python\projects\BangA\hehe\data_json\math_de2024.json','r',encoding='utf-8') as f:
    T = json.load(f)
with open(r'D:\Code\Python\projects\BangA\hehe\data_json\physic_de2024.json','r',encoding='utf-8') as f:
    L = json.load(f)




def get_chapter_lesson_names_by_subject(subject):
   
    with app.app_context():
       
        results = db.session.query(LessonInfo.lesson_num, LessonInfo.lesson_name).filter_by(
            subject=subject
        ).distinct().all() 

        return results  
    
def get_problem_types(id_subject):

    if id_subject == 'H':
        id_subject = 'S3'
    elif id_subject == 'L':
        id_subject = 'S2'
    elif id_subject == 'T':
        id_subject = 'S1'

    result = db.session.query(ProblemTypes.chapter_num, ProblemTypes.problem_types).filter_by(
        id_subject = id_subject
    ).distinct().all()

    return result


def compute_cosine_similarity(query, candidates):

    vectorizer = TfidfVectorizer().fit([query] + candidates)
    
    query_vec = vectorizer.transform([query])
    candidates_vec = vectorizer.transform(candidates)
    
    similarities = cosine_similarity(query_vec, candidates_vec)[0]
    
    return similarities


def process_questions(data, subject):
   
    problem_types = get_problem_types(subject)  # List[Tuple[str, str]]
    lesson_names = get_chapter_lesson_names_by_subject(subject)  # List[Tuple[str, str]]
    
    problem_type_texts = [pt[1] for pt in problem_types]  # Chỉ lấy problem_type
    lesson_name_texts = [ln[1] for ln in lesson_names]  # Chỉ lấy lesson_name
    
    results = []
    
    for i in data:
        id = i['id']
        question = i['question']
        image_source = i['image_source']
        difficulty = i['difficulty']
        options = i['options']
        answer = i['answer']
        explain = i['explain']
        
        similarity_pt = compute_cosine_similarity(question, problem_type_texts)
        
        max_sim_pt_index = similarity_pt.argmax()
        max_sim_pt_score = similarity_pt[max_sim_pt_index]
        selected_problem_type = problem_types[max_sim_pt_index][1]
        selected_chapter_num_pt = problem_types[max_sim_pt_index][0]
        
        similarity_ln = compute_cosine_similarity(selected_problem_type, lesson_name_texts)
        
        max_sim_ln_index = similarity_ln.argmax()
        max_sim_ln_score = similarity_ln[max_sim_ln_index]
        selected_lesson_name = lesson_names[max_sim_ln_index][1]
        selected_chapter_num_ln = lesson_names[max_sim_ln_index][0]
        
        id = f'{subject}{selected_chapter_num_pt}{int(selected_chapter_num_ln):02d}DE1'
        result = {
            'id': id,
            'question': question,
            'image_source': image_source,
            'difficulty': difficulty,
            'options': options,
            'answer': answer,
            'explain': explain
        }
        
        results.append(result)
    
    return results




with app.app_context(): 

    subject = 'H'  
    processed_results = process_questions(H, subject)
    for res in processed_results:
        print(f"{res['id']}")
        print(f"{res['question']}")
        print(f" {res['image_source']}")
        print(f"{res['difficulty']}")
        print(f"{res['options']}")
        print(f"{res['answer']}")
        print(f"{res['explain']}")
        print("-" * 50)
    with open('D:\Code\Python\projects\BangA\hehe\data_json\processed_che_de2024.json','w',encoding='utf-8') as f:
        json.dump(processed_results, f, indent=4,ensure_ascii=False)

    subject = 'T'  
    processed_results = process_questions(T, subject)
    for res in processed_results:
        print(f"{res['id']}")
        print(f"{res['question']}")
        print(f" {res['image_source']}")
        print(f"{res['difficulty']}")
        print(f"{res['options']}")
        print(f"{res['answer']}")
        print(f"{res['explain']}")
        print("-" * 50)
    with open('D:\Code\Python\projects\BangA\hehe\data_json\processed_math_de2024.json','w',encoding='utf-8') as f:
        json.dump(processed_results, f, indent=4,ensure_ascii=False)

    subject = 'L'  
    processed_results = process_questions(L, subject)
    for res in processed_results:
        print(f"{res['id']}")
        print(f"{res['question']}")
        print(f" {res['image_source']}")
        print(f"{res['difficulty']}")
        print(f"{res['options']}")
        print(f"{res['answer']}")
        print(f"{res['explain']}")
        print("-" * 50)
    with open('D:\Code\Python\projects\BangA\hehe\data_json\processed_physic_de2024.json','w',encoding='utf-8') as f:
        json.dump(processed_results, f, indent=4,ensure_ascii=False)