from openai import OpenAI
from dotenv import load_dotenv 
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

load_dotenv()
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
        self.analyze_only_prompt = "Chỉ phân tích và đánh giá, không cần đưa ra kế hoạch cải thiện và khuyến nghị "

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
            next(data)
            for row in data:
                data_prompt += f"Chương {row[0]} có loại câu hỏi {row[1]} với kì vọng là {row[5]}%\n"

        data_prompt += "Dưới đây là trung bình các bài hay sai của các chương:\n"
        lessons_review_dict = self.data.lessons_id_to_review()
        for chap, value in lessons_review_dict.items():
            data_prompt += f"Chương {chap}:"
            for lesson, count in value['lesson'].items():
                data_prompt += f" {lesson} bài, "
        # tìm ra điểm mạnh điểm yếu
        # Điểm số, tgian làm bài cải thiện hay giảm, so sánh với aim score để đánh giá
        # nhận xét về phần làm tốt, phần cần cải thiện
        # nhắc nhở học sinh ôn các bài hay sai trong chương, xem lại các chương sai nhiều
        # đề xuất chiến lược học tập, sử dụng các functions của ứng dụng
        data_prompt += (
            "\nHãy phân tích kỹ lưỡng để tìm ra điểm mạnh và điểm yếu của học sinh:\n"
            "- So sánh kết quả với aim score để đánh giá hiệu quả học tập.\n"
            "- Nhận xét về những phần làm tốt và chỉ ra các phần cần cải thiện.\n"
            "- Nhắc nhở học sinh ôn tập lại các bài thường hay sai, đặc biệt chú ý những chương có tỉ lệ sai cao.\n"
            "- Đề xuất chiến lược học tập để cải thiện các điểm yếu (Chỉ tập trung phân tích, không cần ghi ngày giờ cụ thể), bao gồm việc sử dụng các chức năng của ứng dụng như 'Wrong question searching', 'Analytic review', và 'Practice test recommendation' để hỗ trợ ôn tập.\n"
        )
        return data_prompt



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
            next(data)
            for row in data:
                data_prompt += f"- Chương {row[0]} | Loại câu hỏi {row[1]}: Kỳ vọng {row[5]}%\n"

        data_prompt += (
            "\nPhân tích chi tiết kết quả trên để tìm ra điểm mạnh và điểm yếu của học sinh:\n"
            "- Xác định các phần kiến thức mà học sinh đã nắm vững (điểm số cao, thời gian ngắn).\n"
            "- Nhận diện các phần cần cải thiện (điểm số thấp, thời gian dài).\n"
            "- So sánh kết quả với kỳ vọng để xác định liệu học sinh có đạt được mục tiêu đã đề ra không.\n"
            "- Chú ý đến những chương hoặc loại câu hỏi có tỉ lệ sai cao để tập trung ôn tập.\n"
        )

        data_prompt += (
            "Đưa ra các nhận xét và lời khuyên cụ thể cho học sinh:\n"
            "- Tập trung ôn lại các loại câu hỏi có tỉ lệ đúng thấp.\n"
            "- Chuẩn bị kỹ lưỡng cho bài kiểm tra tiếp theo bằng cách ôn tập các chương có tỉ lệ sai cao.\n"
            "- Đặt mục tiêu cụ thể cho mỗi buổi học, ví dụ: cải thiện điểm số trong các câu hỏi 'Nhận biết' và 'Thông hiểu'. (Chỉ tập trung phân tích, không cần ghi ngày giờ cụ thể)\n"
        )

        data_prompt += self.detail_analyze_prompt
        return data_prompt


class generateAnalysis:
    def __init__(self, subject, num_chap):
        self.configuration = {
            "temperature": 0.8,
            "max_tokens": 5000,
            "top_p": 0.8,
        }
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key)
        self.num_test = 8
        self.subject = subject
        self.num_chap = num_chap
        self.next_test_date = promptTotal("total", self.num_test, self.subject).next_test_date()

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

    def return_prompt(self, analyze_type):
        if analyze_type == "fast":
            prompt = promptTotal("total", self.num_test, self.subject).fast_analysis()
        elif analyze_type == "deep":
            prompt = promptTotal("total", self.num_test, self.subject).deep_analysis()
        elif analyze_type == "progress":
            prompt = promptTotal("total", self.num_test, self.subject).track_progress()
        elif analyze_type == "chapter":
            prompt = promptChap("chapter", self.num_test, self.subject, self.num_chap).chap_analysis()
        else:
            return "Invalid analyze type. Please choose between 'fast', 'deep', 'progress', or 'chapter'."
        return prompt

    def call_gpt(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Replace with the correct model name, such as 'gpt-4' or other supported models
            messages=[
                {"role": "system", "content": "bạn là 1 gia sư, bạn giỏi trong việc đánh giá những số liệu của X bài test total (bài test tổng hợp khi user học đến chương N) hoặc số liệu của X bài test chương (bài test chương N của user), biết N và X là số dương bất kỳ. Nhiệm vụ của bạn là theo prompt được hướng dẫn, bạn hãy generate các phân tích cũng như đánh giá. Và khi cần sẽ là 1 kế hoạch rõ ràng dựa vào đánh giá được cho, kế hoạch này sẽ như 1 to do list và từng ngày sẽ có từng tác vụ cụ thể được hướng dẫn trong prompt. Nếu đang phân tích thì chỉ tập trung phân tích, đừng ghi kế hoạch cụ thể."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.configuration['temperature'],
            max_tokens=self.configuration['max_tokens'],
            top_p=self.configuration['top_p'],
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content

    def analyze(self, analyze_type):
        prompt = self.return_prompt(analyze_type)
        response = self.call_gpt(prompt)
        return response

    def detail_plan_and_timeline(self):
        # Xác định ngày tiếp theo cho test tổng và test chương
        date_total = promptCreation("total", self.num_test, self.subject, self.num_chap).next_test_date()
        date_chap = promptCreation("chapter", self.num_test, self.subject, self.num_chap).next_test_date()
        diff = promptCreation("total", self.num_test, self.subject, self.num_chap).diff_prompt()
        current_date = datetime.now()
        functions = promptCreation("total", self.num_test, self.subject, self.num_chap).functions_prompt
        
        # Bắt đầu xây dựng chuỗi prompt
        prompt = "1. **từ phân tích test tổng:**\n"
        prompt += self.analyze("deep")

        time.sleep(5)  # Thời gian chờ để đảm bảo quá trình tải hoàn tất
        prompt += "\n2. **từ phân tích test chương:**\n"
        prompt += self.analyze("chapter")

        # Gợi ý lập kế hoạch học tập chi tiết
        prompt += (
            f"\n Ôn tập theo những thành phần được nêu sau:\n"
            f"1. Ôn lại kiến thức cũ, đặc biệt là những phần còn yếu.\n"
            f"2. Chuẩn bị học chương {self.num_chap + 1} để sẵn sàng cho bài test chương tiếp theo.\n"
            f"3. Tập trung cải thiện điểm yếu đã chỉ ra ({diff}), sử dụng các chức năng của ứng dụng ({functions}).\n"
            f"4. Đặc biệt nhắc học sinh chuẩn bị cho bài test chương {self.num_chap + 1} vào ngày {date_chap}.\n"
            f"5. Lập lịch ôn tập để chuẩn bị cho bài test tổng vào ngày {date_total}, bắt đầu từ {current_date.strftime('%d/%m/%Y')}.\n"
            f"6. Mỗi ngày có nhiệm vụ rõ ràng, đảm bảo ôn tập hiệu quả.\n"
        )
        prompt += (
        "Hãy viết theo format sau, mỗi nhiệm vụ riêng biệt cho từng ngày:\n"
        "'ngày xx/tháng xx/năm xxxx : làm gì đó'\n")
        # Yêu cầu format cụ thể cho kế hoạch học tập

        response = self.call_gpt(prompt)
        return response

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
        response = self.call_gpt(prompt)
        return response