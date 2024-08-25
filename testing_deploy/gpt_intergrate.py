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
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import timedelta
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
        self.functions_prompt = f"Biết rằng app có 1 số chức năng như: practice test recommendation (đây là 1 bài test gồm những kiến thức đã sai từ {self.num_chap} chương trước), Analytic review (review phần analysis của {self.num_test} bài test, tìm ra được điểm mạnh yếu trong kiến thức và đánh giá chung bài test), Wrong question searching (chức năng xem lại tất cả các bài đã sai)\n"

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
            f"biết rằng thời gian tối ưu 2 bài test cách là {self.data.time_to_do_test} ngày, "
            f"với aim điểm là {self.aim_score} thì user có kịp tiến độ ko, với "
            f"dữ liệu được đưa vào như sau:\n"
        )
        results, _, exact_time, nums = self.data.previous_results()
        for i in range(len(results)):
            data_prompt += f"{results[i]/nums[i]*10} at {exact_time[i]}\n"
        data_prompt += self.analyze_only_prompt
        return data_prompt
    def diff_prompt(self):
        return "\nChú thích cho loại câu hỏi: 1 là Nhận biết, 2 là Thông hiểu, 3 là vận dụng, 4 là vận dụng cao\n" 
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
    def next_test_date(self):
        # Load the completion time from the JSON file
        with open(f"{self.subject}_{self.type_test}_results.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            date = data[-1]['completion_time']
        
        date = pd.to_datetime(date)  # Convert to datetime object
        print(self.data.time_to_do_test)
        return date + self.data.time_to_do_test


class promptTotal(promptCreation):
    def __init__(self, type_test, num_test, subject):
        super().__init__(type_test, num_test, subject)
        self.prompt_score = "(cho biết kết quả ở hệ số 10)"
        self.analyze_only_prompt = "Chỉ phân tích và đánh giá, không cần đưa ra kế hoạch cải thiện và khuyến nghị"

    def fast_analysis(self):
        data_prompt = self.test_intro
        data_prompt += (
            f"{self.prompt} {self.subject_intro} và với lượng dữ liệu được đưa vào như sau ({self.prompt_score} và thời gian thực hiện chúng), "
            f"hãy phân tích và đánh giá kết quả của bài test vừa thực hiện so với các lần làm test total trước đó, "
            f"để xác định các xu hướng học tập và đánh giá sự tiến bộ của học sinh theo thời gian. "
            f"Dữ liệu được đưa vào như sau:\n"
        )

        results, durations, exact_time, nums = self.data.previous_results()
        for i in range(len(results)):
            data_prompt += f"Điểm: {results[i]/nums[i]*10} Thời gian thực hiện: {durations[i]} giây, Thời điểm thực hiện: {exact_time[i]}\n"

        data_prompt += (
            "Vui lòng so sánh các kết quả này để xác định sự tiến bộ của học sinh qua thời gian. "
            "Những lần nào học sinh có sự cải thiện về điểm số và thời gian làm bài, và những lần nào không? "
            "Những yếu tố nào có thể đã ảnh hưởng đến kết quả, chẳng hạn như thời gian làm bài, số lượng bài tập ôn luyện, hoặc các yếu tố bên ngoài? "
        )
        data_prompt += self.analyze_only_prompt
        data_prompt += "Đánh giá tổng quan về hiệu quả học tập và đưa ra các khuyến nghị cụ thể cho học sinh."
        return data_prompt

    def deep_analysis(self):
        data_prompt = (
            f"{self.test_intro} {self.prompt} {self.subject_intro} và tất cả lượng dữ liệu sau được lấy trung bình từ {self.num_test} bài test total trước đó\n"
            "Dưới đây là tỉ lệ % đúng và thời gian làm bài của từng chương:\n"
        )
        acuc_chaps, time_chaps = self.data.short_total_analysis()
        for key, value in acuc_chaps.items():
            data_prompt += f"Chương {key}: {value}% - {time_chaps[key]} giây\n"

        data_prompt += self.diff_prompt()
        data_prompt += "Tỉ lệ % đúng của từng loại câu hỏi:\n"
        accu_diff, dic_ques, dic_total = self.data.cal_accu_diff()
        for type1, accu in accu_diff.items():
            data_prompt += f"Loại câu hỏi {type1}: {accu}%\n"

        data_prompt += "Tỉ lệ % đúng của các loại câu hỏi từng chương:\n"
        chap_difficulty_percentile = self.data.difficult_percentile_per_chap()
        for chap, dic_diff in chap_difficulty_percentile.items():
            data_prompt += f"Chương {chap}:\n"
            for type1, acuc in dic_diff.items():
                data_prompt += f"- Loại câu hỏi {type1}: {acuc}%\n"

        data_prompt += "So sánh với kì vọng % đúng của các loại câu hỏi từng chương:\n"
        with open(f"{self.subject}_{self.type_test}_threshold.csv", "r", encoding='utf-8') as file:
            data = csv.reader(file)
            for row in data:
                data_prompt += f"Chương {row[0]} có loại câu hỏi {row[1]} với kì vọng là {row[2]}%\n"

        data_prompt += "Dưới đây là trung bình các bài hay sai của các chương:\n"
        lessons_review_dict = self.data.lessons_id_to_review()
        for chap, value in lessons_review_dict.items():
            data_prompt += f"Chương {chap}:"
            for lesson, count in value['lesson'].items():
                data_prompt += f" {lesson} bài,"

        data_prompt += (
            "\nVui lòng so sánh kỹ lưỡng các giá trị trên để tìm ra điểm mạnh và điểm yếu của học sinh. "
            "Điểm số và thời gian làm bài có xu hướng cải thiện hay giảm sút? "
            "So sánh các kết quả với aim score để đánh giá liệu học sinh có đạt được mục tiêu học tập hay không. "
            "Đưa ra các nhận xét cụ thể về các phần học sinh làm tốt, các phần cần cải thiện, và những gì học sinh cần tập trung hơn để cải thiện kết quả. "
            "Hãy đề xuất các chiến lược học tập, bao gồm cả việc sử dụng các chức năng của ứng dụng, để học sinh có thể cải thiện điểm số trong các bài kiểm tra tiếp theo."
        )
        return data_prompt

    def detail_plan_and_timeline(self):
        plan_prompt = self.fast_analysis() + self.deep_analysis()
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%Y-%m-%d")
        plan_prompt += f"Đa dạng hóa kế hoạch chi tiết ôn tập những kiến thức yếu cho cả {self.num_chap} chương\n"
        plan_prompt += self.functions_prompt
        plan_prompt += f"và điểm hiện tại là {formatted_date} và thời điểm làm bài test total tiếp theo là {self.next_test_date()}, đa dạng hóa kế hoạch theo format sau: 'ngày/tháng/năm : kế hoạch cụ thể'\n"
        return plan_prompt


class promptChap(promptCreation):
    def __init__(self, type_test,num_test,subject,num_chap):
        super().__init__(type_test, num_test,subject,num_chap)
    def chap_analysis(self):
        data_prompt = (
            f"{self.test_intro} {self.prompt} {self.subject_intro}. "
            f"Tất cả các dữ liệu dưới đây được lấy trung bình từ {self.num_test} bài test chương {self.num_chap} trước đó.\n"
            "Dưới đây là tỷ lệ % đúng và thời gian làm bài của từng lần làm bài trước đó. Dòng dữ liệu cuối cùng là kết quả của lần thực hiện gần đây nhất:\n"
        )

        results, durations, exact_time, nums = self.data.previous_results()
        for i in range(len(results)):
            data_prompt += f"- Điểm: {results[i]/nums[i]*10} | Thời gian thực hiện: {durations[i]} giây | Thời điểm thực hiện: {exact_time[i]}\n"

        data_prompt += "\nPhân tích tỉ lệ % đúng của từng loại câu hỏi trong chương:\n"
        data_prompt += self.diff_prompt()
        accu_diff, dic_ques, dic_total = self.data.cal_accu_diff()
        for type1, accu in accu_diff.items():
            data_prompt += f"- Loại câu hỏi {type1}: {accu}%\n"

        data_prompt += "\nSo sánh tỉ lệ % đúng hiện tại với kỳ vọng của từng loại câu hỏi trong chương:\n"
        with open(f"{self.subject}_{self.type_test}_threshold.csv", "r", encoding='utf-8') as file:
            data = csv.reader(file)
            for row in data:
                data_prompt += f"- Chương {row[0]} | Loại câu hỏi {row[1]}: Kỳ vọng {row[2]}%\n"

        data_prompt += (
            "\nVui lòng phân tích kỹ lưỡng những điểm mạnh và điểm yếu của học sinh dựa trên các kết quả này. "
            "So sánh kết quả với kỳ vọng để xác định các lĩnh vực học sinh đã vượt qua hoặc chưa đạt được. "
            "Đưa ra các nhận xét cụ thể về các kỹ năng học sinh đã nắm vững và các kỹ năng còn cần phải cải thiện.\n"
        )

        data_prompt += (
            "Dựa trên các phân tích trên, hãy đưa ra lời khuyên cụ thể cho học sinh về cách cải thiện kết quả trong các lần làm bài sau. "
            "Đề xuất các chiến lược học tập, như tập trung vào các loại câu hỏi còn yếu, hoặc sử dụng các chức năng của ứng dụng để ôn luyện.\n"
        )

        data_prompt += self.detail_analyze_prompt
        return data_prompt
    def chap_plan(self):
        plan_prompt = self.chap_analysis()
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%Y-%m-%d")
        plan_prompt += f"\nĐa dạng hóa kế hoạch chi tiết ôn tập những điểm yếu cho bài test chương {self.num_chap}\n"
        plan_prompt += self.functions_prompt
        plan_prompt += f"và điểm hiện tại là {formatted_date} và thời điểm làm bài test chương tiếp theo là {self.next_test_date()}, đa dạng hóa kế hoạch theo format sau: 'ngày/tháng/năm : kế hoạch cụ thể'\n"
        return plan_prompt


class generateAnalysis:
    def __init__(self,subject,num_chap):
        self.configuration = {
            "temperature" : 0.7,
            "top_p" : 0.9,
            "top_k" : 80,
            "max_output_tokens" : 5000
        }
        self.model_name = 'gemini-1.5-pro-latest'
        self.gg_api_key = 'AIzaSyCPWag7mBUXOMmFTcmyi0vhz1sdYdTvMZA'
        genai.configure(api_key=self.gg_api_key)
        self.model = genai.GenerativeModel(self.model_name, generation_config=self.configuration)
        self.num_test = 8
        self.subject = subject
        self.num_chap = num_chap
        self.next_test_date = promptTotal("total",self.num_test,self.subject).next_test_date()
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
        # Xác định ngày tiếp theo cho test tổng và test chương
        date_total = promptCreation("total", self.num_test, self.subject, self.num_chap).next_test_date()
        date_chap = promptCreation("chapter", self.num_test, self.subject, self.num_chap).next_test_date()
        diff = promptCreation("total", self.num_test, self.subject, self.num_chap).diff_prompt()
        current_date = datetime.now()
        functions = promptCreation("total", self.num_test, self.subject, self.num_chap).functions_prompt
        
        # Bắt đầu xây dựng chuỗi prompt
        prompt = "1. **từ phân tích test tổng:**\n"
        prompt += self.analyze_deep()

        time.sleep(5)  # Thời gian chờ để đảm bảo quá trình tải hoàn tất
        prompt += "\n2. **từ phân tích test chương:**\n"
        prompt += self.analyze_chapter()

        # Gợi ý lập kế hoạch học tập chi tiết
        prompt += (
            f"1. Ôn lại kiến thức cũ, đặc biệt là những phần còn yếu.\n"
            f"2. Chuẩn bị học chương {self.num_chap + 1} để sẵn sàng cho bài test chương tiếp theo.\n"
            f"3. Tập trung cải thiện điểm yếu đã chỉ ra ({diff}), sử dụng các chức năng của ứng dụng ({functions}).\n"
            f"4. Ghi chú lỗi sai và nhắc học sinh chuẩn bị cho bài test chương {self.num_chap + 1} vào ngày {date_chap}.\n"
            f"5. Lập lịch ôn tập để chuẩn bị cho bài test tổng vào ngày {date_total}, bắt đầu từ {current_date.strftime('%d/%m/%Y')}.\n"
            f"6. Mỗi ngày có nhiệm vụ rõ ràng, đảm bảo ôn tập hiệu quả.\n"
        )
        prompt += (
        "Hãy viết theo format sau, mỗi nhiệm vụ riêng biệt cho từng ngày:\n"
        "'ngày xx/tháng xx/năm xxxx : làm gì đó'\n")
        # Yêu cầu format cụ thể cho kế hoạch học tập

        response = self.model.generate_content(prompt)
        return response.text

    def format_data(self):
        data = self.detail_plan_and_timeline()
        prompt = (
            f"Từ {data} hãy format lại thành 1 file JSON với các mục sau cho mỗi nhiệm vụ:\n"
            f"- 'date': Ngày tháng cụ thể của nhiệm vụ (ví dụ: '24/08/2024')\n"
            f"- 'action': Mô tả nhiệm vụ cần làm (ví dụ: 'Phân tích kết quả bài test')\n"
            f"- 'done': Trạng thái của nhiệm vụ, luôn là 'false' khi chưa hoàn thành\n"
            f"Ví dụ:\n"
            f"[{{'date': '24/08/2024', 'action': 'Phân tích kết quả bài test', 'done': 'false'}}]\n"
            f"Đây là dữ liệu cần format lại:\n"
            f"'{data}'\n"
        )
        response = self.model.generate_content(prompt)
        return response.text