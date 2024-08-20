import openai

openai.api_key = ""


import requests

# URL = "https://api.openai.com/v1/chat/completions"

# payload = {
# "model": "gpt-3.5-turbo",
# "messages": [{"role": "user", "content": f"What is the first computer in the world?"}],
# "temperature" : 1.0,
# "top_p":1.0,
# "n" : 1,
# "stream": False,
# "presence_penalty":0,
# "frequency_penalty":0,
# }

# headers = {
# "Content-Type": "application/json",
# "Authorization": f"Bearer {openai.api_key}"
# }

# response = requests.post(URL, headers=headers, json=payload, stream=False)
# print(response.content)

# Import the Python SDK


import os
import google.generativeai as genai
from pathlib import Path
from chart_drawing2 import DrawTotal, DrawChap

# image_path = Path("images.jpg")
# image_part = {
#     "mime_type" : "image/jpeg",
#     "data" : image_path.read_bytes()
# }


# prompt_parts = [
#     "Describe the picture\n",
#     image_part
# ]

# response = model.generate_content(prompt_parts)

# print(response.text)




# prompt creation
class promptCreation:
    def __init__(self, type_test, num_test, subject):
        self.type_test = type_test
        self.num_test = num_test
        self.prompt = "Bạn là một gia sư dạy kèm"
        self.final_exam_date = "2025-07-12"
        self.subject = subject
        self.aim_score = 9
        self.data = DrawTotal(self.subject, None, self.type_test, self.num_test) if self.type_test == "total" else DrawChap(self.subject, None, self.type_test, self.num_test)
        self.test_intro = self.get_test_intro()

        # Correctly instantiate the data object based on type_test
        
    def return_subject_name(self):
        name = {
            "T": "Toán",
            "L": "Lý",
            "H": "Hóa",
            "S": "Sinh",
            "V": "Văn",
            "A": "Anh",
        }
        return name.get(self.subject, "Unknown Subject")

    def get_test_intro(self):
        if self.type_test == "total":
            return f"Đây là kết quả {self.type_test} test, là bài test tất cả các chương đã học tính đến hiện tại là {self.data.num_chap}."
        elif self.type_test == "chapter":
            return f"Đây là kết quả {self.type_test} test, là bài test chương {self.data.num_chap}."

    def previous_result(self):
        data_prompt = self.test_intro
        data_prompt += (
            f"{self.prompt}, Đây là kết quả môn {self.subject}, từ đó hãy Phân tích kết quả kiểm tra {self.prompt_score} và thời gian thực hiện chúng. "
            f"Từ đó cho ra nhận xét nó có kịp tiến độ hay không, "
            f"biết rằng thời gian tối ưu 2 bài test cách là {self.data.time_to_do_test} tháng, "
            f"với aim điểm là {self.aim_score} thì user có kịp tiến độ ko, với "
            f"dữ liệu được đưa vào như sau:\n"
        )
        results, _, exact_time, nums = self.data.previous_results()
        for i in range(len(results)):
            data_prompt += f"{results[i]/nums[i]*10} at {exact_time[i]}\n"
        data_prompt += self.analyze_only_prompt
        return data_prompt
    def diff_prompt(self):
        return "\nChú thích cho loại câu hỏi: 1 là Thông hiểu, 2 là nhận biết, 3 là vận dụng, 4 là vận dụng cao\n" 

class promptTotal(promptCreation):
    def __init__(self, type_test, num_test, subject):
        super().__init__(type_test, num_test, subject)
        self.prompt_score = "(cho biết kết quả ở hệ số 10)"
        self.subject = self.return_subject_name()
        self.subject_intro = f"Đây là kết quả môn {self.subject}"
        self.analyze_only_prompt = "Chỉ phân tích và đánh giá, không cần đưa ra kế hoạch cải thiện và khuyến nghị"

    def fast_analysis(self):
        data_prompt = self.test_intro
        data_prompt += (
            f"{self.prompt} {self.subject_intro} và với lượng dữ liệu được đưa vào như sau ({self.prompt_score} và thời gian thực hiện chúng), "
            f"hãy phân tích và đánh giá kết quả vừa thực hiện với các lần làm test total trước đó, "
            f"biết rằng data cuối cùng là kết quả vừa thực hiện và các data trước đó là kết quả đã thực hiện trước đó. "
            f"Dữ liệu được đưa vào như sau:\n"
        )

        results, durations, exact_time, nums = self.data.previous_results()
        for i in range(len(results)):
            data_prompt += f"Điểm: {results[i]/nums[i]*10} Thời gian thực hiện: {durations[i]} Thời điểm thực hiện: {exact_time[i]}\n"
        data_prompt += self.analyze_only_prompt
        data_prompt += "Đánh giá vừa đủ lượng dữ liệu được cho"
        return data_prompt

    def deep_analysis(self):
        data_prompt = (f"{self.test_intro} {self.prompt} {self.subject_intro}")
        # tỉ lệ thể hiện % đúng của từng chương + thời gian
        data_prompt += (f"Sau đây là tỉ lệ % đúng và thời gian làm bài của từng chương\n")
        acuc_chaps, time_chaps = self.data.short_total_analysis()
        for i in range(len(acuc_chaps)):
            data_prompt += f"Chương {i+1}: {acuc_chaps[i]}% - {time_chaps[i]} giây\n"
        # thể hiện % đúng của từng loại câu hỏi TH, NB, VD ,VDC
        data_promp += self.diff_prompt()
        data_prompt += "Sau đây là % đúng của từng loại câu hỏi\n"
        accu_diff, dic_ques, dic_total = self.data.cal_accu_diff()
        for type1, accu in accu_diff.items():
            data_prompt += f"Loại câu hỏi {type1}: {accu}%\n"
        # so sánh với threshold
        

        # Chương nào sai nhiều nhất,% đúng của TH,NB,  VD , VDC từng chương 
        data_prompt += "Sau đây là % đúng của các loại câu hỏi từng chương\n"
        chap_difficulty_percentile = self.data.difficult_percentile_per_chap()
        for chap, dic_diff in chap_difficulty_percentile.items():
            data_promp += f"Đối với chương {chap}"
            for type1, acuc in dic_diff.items():
                data_prompt += f"Loại câu hỏi {type1}: {acuc}%\n"
        # trung bình các bài hay sai của các chương
        data_prompt += "Sau đây là trung bình các bài hay sai của các chương\n"
        lessons_review_dict = self.data.lessons_id_to_review()
        for chap, values[0] in lessons_review_dict.items():
            data_prompt += f"Chương {chap}: {values[0]} bài\n"
        

        # tong ket
        #⇒ Nhận xét: Mạnh phần nào/ yếu phần nào
        # ⇒ khen thưởng, nhắc nhở 
        #⇒ đưa ra lời khuyên
        return None

    def detail_plan(self):
        # Implement this if needed
        return None

    def detail_timeline(self):
        # Implement this if needed
        return None

class promptChap(promptCreation):
    def __init__(self, type_test,num_test,subject,data):
        super().__init__(type_test, num_test,subject)
    def chap_analysis(self):
        return None

class generateAnalysis:
    def __init__(self,subject):
        self.configuration = {
            "temperature" : 0.7,
            "top_p" : 0.8,
            "top_k" : 50,
            "max_output_tokens" : 2048
        }
        self.model_name = 'gemini-1.5-pro-latest'
        self.gg_api_key = ''
        genai.configure(api_key=self.gg_api_key)
        self.model = genai.GenerativeModel(self.model_name, generation_config=self.configuration)
        self.num_test = 8
        self.subject = subject
    def analyze_progress(self):
        prompt = promptTotal("total",self.num_test,self.subject).track_progress()
        response = self.model.generate_content(prompt)
        return response.text
    def analyze_fast(self):
        prompt = promptTotal("total",self.num_test,self.subject).fast_analysis()
        response = self.model.generate_content(prompt)
        return response.text
    
# test = generateAnalysis("T")
# # print(test.analyze_progress())
# print(test.analyze_fast())