from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv 
import os
from openai import OpenAI
load_dotenv()
app = Flask(__name__)

# Set up OpenAI API credentials
api_key = os.getenv('OPENAI_API_KEY')


# Define the default route to return the index.html file
@app.route("/")
def index():
    return render_template("index.html")

# Define the /api route to handle POST requests


data = r"""
\section*{Bài 1: TÍNH ĐƠN ĐIỆU CỦA HÀM SỐ}

\textbf{1. Định nghĩa:} Giả sử hàm số $y = f(x)$ xác định trên tập $K$.
\begin{itemize}
    \item Hàm số $y = f(x)$ được gọi là đồng biến trên $K$ nếu $\forall x_1, x_2 \in K, x_1 < x_2 \Rightarrow f(x_1) < f(x_2)$.
    \item Hàm số $y = f(x)$ được gọi là nghịch biến trên $K$ nếu $\forall x_1, x_2 \in K, x_1 < x_2 \Rightarrow f(x_1) > f(x_2)$.
\end{itemize}

\textbf{2. Định lý mở rộng:}
\begin{itemize}
    \item Nếu $f'(x) > 0$ thì hàm số $y = f(x)$ đồng biến trên khoảng $I$.
    \item Nếu $f'(x) < 0$ thì hàm số $y = f(x)$ nghịch biến trên khoảng $I$.
\end{itemize}

\textbf{3. Phương pháp:}
\begin{itemize}
    \item Bước 1: Tìm tập xác định.
    \item Bước 2: Tính $y'$ và giải $y' = 0$.
    \item Bước 3: Lập bảng biến thiên.
    \item Bước 4: Kết luận.
\end{itemize}

\textbf{4. Hình dáng đồ thị:}
\begin{itemize}
    \item Nếu hàm số đồng biến thì đồ thị hàm số đi lên (trái sang phải).
    \item Nếu hàm số nghịch biến thì đồ thị hàm số đi xuống (trái sang phải).
\end{itemize}
"""
client = OpenAI(api_key=api_key)
@app.route("/api", methods=["POST"])
def api():
    # Get the message from the POST request

    message = request.json.get("message")
    # Send the message to OpenAI's API and receive the response
    
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Bạn là 1 gia sư giải thích lý thuyết bài học cho học sinh, sau đây là phần lý thuyết của bài học học sinh chuẩn bị hỏi: {data} "},
            {"role": "user", "content": message}
        ]
    )
    print(completion.choices[0].message.content)
    if completion.choices[0].message!=None:
        content = completion.choices[0].message.content
        return jsonify({"response": content})

    else :
        return 'Failed to Generate response!'
    

if __name__=='__main__':
    app.run(debug=True)

