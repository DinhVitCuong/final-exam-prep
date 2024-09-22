import re

def extract_question(block_cleaned):
    # Sửa biểu thức chính quy để bắt được cả trường hợp \section*{Câu X} hoặc "Câu X" mà vẫn có thể xuống dòng
    question_match = re.search(r"Câu \d+\s*(.*?)\s*(?=[A-D]\.\s)", block_cleaned, re.DOTALL)
    
    if question_match is None:
        question_match = re.search(r"\\section\*\{Câu \d+\}\s*(.*?)\s*(?=[A-D]\.\s)", block_cleaned, re.DOTALL)

    # Trả về câu hỏi đã được trim khoảng trắng nếu tìm thấy
    question = question_match.group(1).strip() if question_match else None
    return question

# Đoạn văn bản đã làm sạch
block_cleaned = r"""
\section*{L0707033}
Câu 3

Phản ứng phân hạch là\\
A. phản ứng trong đó một hạt nhân có số khối nhỏ vỡ thành hai mảnh nhẹ hơn.\\
D. sự kết hợp hai hạt nhân có số\\
khối trung bình tạo thành hạt nhân nặng hơn.\\
B. phản ứng hạt nhân thu năng lượng.\\
C. phản ứng trong đó một hạt nhân nặng vỡ thành hai mảnh nhẹ hơn.

\section*{Lời giải của GV Loigiaihay.com}
Phản ứng phân hạch là phản ứng trong đó một hạt nhân nặng vỡ thành hai mảnh nhẹ hơn
"""

# Gọi hàm để trích xuất câu hỏi
question = extract_question(block_cleaned)
print(question)