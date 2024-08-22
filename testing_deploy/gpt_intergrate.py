import openai
import json
import requests
import os
import google.generativeai as genai
from pathlib import Path
from chart_drawing2 import DrawTotal, DrawChap
from predict_threshold import prepThreshold, predictThreshold
import csv
from datetime import datetime
import time 
# prompt creation
class promptCreation:
    def __init__(self, type_test, num_test, subject, num_chap = None):
        self.type_test = type_test
        self.num_test = num_test
        self.num_chap = num_chap
        self.prompt = "Bạn là một gia sư dạy kèm"
        self.final_exam_date = "2025-06-27"
        self.subject = subject
        self.aim_score = 9
        self.data = DrawTotal(self.subject, None, self.type_test, self.num_test) if self.type_test == "total" else DrawChap(self.subject, self.num_chap, self.type_test, self.num_test)
        self.test_intro = self.get_test_intro()
        self.subject_intro = f"Đây là kết quả môn {self.return_subject_name()}"
        self.detail_analyze_prompt = (f"Lưu ý là thêm số liệu cụ thể để phân tích cho kĩ lưỡng nha, Từ đó đưa ra nhận xét về kết quả vừa thực hiện (mạnh phần nào, yếu phần nào, "
        f"phần nào cần được cải thiện, so sánh với các kết quả trước để khen thưởng, nhắc nhở\n"
        f"Đưa ra lời khuyên cụ thể cho user để cải thiện kết quả hơn\n")
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
    def date_time_test(self):
        if self.type_test == "total":
            with open(f"{self.subject}_{self.type_test}_results.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                date = data[-1]['completion_time']
        else:
            with open(f"{self.subject}_{self.type_test}_results.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                date = data[-1]['completion_time']

        return f"Thời điểm làm bài test {self.type_test} cuối cùng là {date}"

class promptTotal(promptCreation):
    def __init__(self, type_test, num_test, subject):
        super().__init__(type_test, num_test, subject)
        self.prompt_score = "(cho biết kết quả ở hệ số 10)"
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
            data_prompt += f"Điểm: {results[i]/nums[i]*10} Thời gian thực hiện: {durations[i]} giây, Thời điểm thực hiện: {exact_time[i]}\n"
        data_prompt += self.analyze_only_prompt
        data_prompt += "Đánh giá vừa đủ lượng dữ liệu được cho"
        return data_prompt

    def deep_analysis(self):
        data_prompt = (f"{self.test_intro} {self.prompt} {self.subject_intro} và tất cả lượng dữ liệu sau được lấy trung bình từ {self.num_test} bài test total trước đó\n")
        # tỉ lệ thể hiện % đúng của từng chương + thời gian
        data_prompt += (f"Sau đây là tỉ lệ % đúng và thời gian làm bài của từng chương\n")
        acuc_chaps, time_chaps = self.data.short_total_analysis()
        for key, value in acuc_chaps.items():
            data_prompt += f"Chương {key}: {value}% - {time_chaps[key]} giây\n"
        # thể hiện % đúng của từng loại câu hỏi TH, NB, VD ,VDC
        data_prompt += self.diff_prompt()
        data_prompt += "Sau đây là % đúng của từng loại câu hỏi\n"
        accu_diff, dic_ques, dic_total = self.data.cal_accu_diff()
        for type1, accu in accu_diff.items():
            data_prompt += f"Loại câu hỏi {type1}: {accu}%\n"

        # Chương nào sai nhiều nhất,% đúng của TH,NB,  VD , VDC từng chương 
        data_prompt += "Sau đây là % đúng của các loại câu hỏi từng chương\n"
        chap_difficulty_percentile = self.data.difficult_percentile_per_chap()
        for chap, dic_diff in chap_difficulty_percentile.items():
            data_prompt += f"Đối với chương {chap}"
            for type1, acuc in dic_diff.items():
                data_prompt += f"Loại câu hỏi {type1}: {acuc}%\n"
        

        # so sánh với threshold
        data_prompt += "So sánh với kì vọng % đúng của các loại câu hỏi từng chương: \n"
        with open(f"{self.subject}_{self.type_test}_threshold.csv", "r", encoding = 'utf-8') as file:
            data = csv.reader(file)
            for row in data:
                data_prompt += f"Chương {row[0]} có loại câu hỏi {row[1]} với kì vọng là {row[2]}\n"


        # trung bình các bài hay sai của các chương
        data_prompt += "Sau đây là trung bình các bài hay sai của các chương\n"
        lessons_review_dict = self.data.lessons_id_to_review()
        for chap, value in lessons_review_dict.items(): # bi loi o day
            for lesson in value['lesson'].keys():
                data_prompt += f"Chương {chap}: {lesson} bài\n"
        data_prompt += self.detail_analyze_prompt
        
        # tong ket
        #⇒ Nhận xét: Mạnh phần nào/ yếu phần nào
        # ⇒ khen thưởng, nhắc nhở 
        #⇒ đưa ra lời khuyên
        return data_prompt

    def detail_plan_and_timeline(self):
        plan_prompt = self.fast_analysis() + self.deep_analysis()
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%Y-%m-%d")
        plan_prompt += "Chỉ cần đưa ra kế hoạch chi tiết để cải thiện và thời gian cụ thể thực hiện chúng"
        plan_prompt += f"Biết rằng app có 1 số chức năng như: làm bài kiểm tra các loại câu đã sai, review lại phân tích, search được các câu đã sai\n"
        plan_prompt += f"và điểm hiện tại là {formatted_date} và {self.date_time_test()}, không cần phân tích và hãy đưa ra kế hoạch theo format sau: 'ngày/tháng/năm : kế hoạch cụ thể'\n"
        return plan_prompt


class promptChap(promptCreation):
    def __init__(self, type_test,num_test,subject,num_chap):
        super().__init__(type_test, num_test,subject,num_chap)
    def chap_analysis(self):
        data_prompt = data_prompt = (f"{self.test_intro} {self.prompt} {self.subject_intro} và tất cả lượng dữ liệu sau được lấy trung bình từ {self.num_test} bài test chương {self.num_chap} trước đó\n")
        # Phân tích trung bình điểm số, thời gian, thời điểm so với các lần làm chương trước đó
        data_prompt += "Sau đây là tỉ lệ % đúng và thời gian làm bài của từng attempt trước đó, biết rằng dòng data cuối là thời điểm vừa thực hiện\n"
        results, durations, exact_time, nums = self.data.previous_results()
        for i in range(len(results)):
            data_prompt += f"Điểm: {results[i]/nums[i]*10} Thời gian thực hiện: {durations[i]} giây, Thời điểm thực hiện: {exact_time[i]}\n"
        # Phân tích trung bình % đúng trong các câu TH, NB, VD , VDC trong chương
        data_prompt += (f"Sau đây là trung bình tỉ lệ % đúng của từng loại câu hỏi trong chương\n")
        data_prompt += self.diff_prompt()
        accu_diff, dic_ques, dic_total = self.data.cal_accu_diff()
        for type1, accu in accu_diff.items():
            data_prompt += f"Loại câu hỏi {type1}: {accu}%\n"
        # So sánh trung bình accuracy các loại câu hỏi trong chương với threshold định sẵn
        data_prompt += "So sánh với kì vọng % đúng của các loại câu hỏi trong chương: \n"
        with open(f"{self.subject}_{self.type_test}_threshold.csv", "r", encoding = 'utf-8') as file:
            data = csv.reader(file)
            for row in data:
                data_prompt += f"Chương {row[0]} có loại câu hỏi {row[1]} với kì vọng là {row[2]}\n"
        data_prompt += self.detail_analyze_prompt
        return data_prompt
    def chap_plan(self):
        data_prompt = self.chap_analysis()
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%Y-%m-%d")
        data_prompt += "Chỉ cần đưa ra kế hoạch chi tiết để cải thiện và thời gian cụ thể thực hiện chúng"
        data_prompt += f"Biết rằng app có 1 số chức năng như: làm bài kiểm tra các loại câu đã sai, review lại phân tích, search được các câu đã sai\n"
        data_prompt += f"và thời điểm hiện tại là {formatted_date} và {self.date_time_test()}, không cần phân tích và hãy đưa ra kế hoạch theo format sau: 'ngày/tháng/năm : kế hoạch cụ thể'\n"
        # Đưa ra kế hoạch cụ thể để cải thiện kết quả trong chương
        # Đưa ra thời gian cụ thể thực hiện kế hoạch
        return data_prompt


class generateAnalysis:
    def __init__(self,subject,num_chap):
        self.configuration = {
            "temperature" : 0.7,
            "top_p" : 0.8,
            "top_k" : 200,
            "max_output_tokens" : 4096
        }
        self.model_name = 'gemini-1.5-pro-latest'
        self.gg_api_key = 'AIzaSyBBkrD1o2ZMfXDp-pM-3sBTkCUKj6bwmsA'
        genai.configure(api_key=self.gg_api_key)
        self.model = genai.GenerativeModel(self.model_name, generation_config=self.configuration)
        self.num_test = 8
        self.subject = subject
        self.num_chap = num_chap
    def analyze_progress(self):
        prompt = promptTotal("total",self.num_test,self.subject).track_progress()
        response = self.model.generate_content(prompt)
        return response.text
    def analyze_fast(self):
        prompt = promptTotal("total",self.num_test,self.subject).fast_analysis()
        response = self.model.generate_content(prompt)
        return response.text
    def analyze_deep(self):
        prompt = promptTotal("total",self.num_test,self.subject).deep_analysis()
        response = self.model.generate_content(prompt)
        return response.text
    def total_plan(self):
        prompt = promptTotal("total",self.num_test,self.subject).detail_plan_and_timeline()
        response = self.model.generate_content(prompt)
        return response.text
    def analyze_chapter(self):
        prompt = promptChap("chapter",self.num_test,self.subject,self.num_chap).chap_analysis()
        response = self.model.generate_content(prompt)
        return response.text
    def chap_plan(self):
        prompt = promptChap("chapter",self.num_test,self.subject,self.num_chap).chap_plan()
        response = self.model.generate_content(prompt)
        return response.text
    def detail_plan_and_timeline(self):

        prompt = ("Hãy gộp lại thành 1 to do list hoàn thiện từ 2 to do list sau, nhấn mạnh là không cần ghi phân tích, \n"
        "hãy viết theo format sau: \n"
            "'ngày xx /tháng xx /năm xxxx : làm 1 cái gì đó'\n",
            "ngày xx /tháng xx /năm xxxx : làm 1 cái gì đó, v.v '\n",)
        # Start building the prompt string
        prompt = "to do list từ phân tích test tổng: "
        prompt += self.total_plan()
        
        prompt += "to do list từ phân tích test chương: "
        time.sleep(5)
        prompt += self.chap_plan()
        
        
        # co 2 huong, lay phan tich cua test chap voi test total de dua ra kế hoạch cụ thể
        # lay chung chung ke hoahc cu the cua test total va test chuong

        # them attribute la : day dang la tuan thu may on thi ... , vv
        return prompt
# test = generateAnalysis("T")
# # print(test.analyze_progress())
# print(test.analyze_fast())