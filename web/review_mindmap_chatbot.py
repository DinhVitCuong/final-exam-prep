from openai import OpenAI
from dotenv import load_dotenv 
import json
import requests
import os
from chart_drawing_sql import DrawTotal, DrawChap
from predict_threshold_sql import PrepThreshold, PredictThreshold
import csv
from datetime import datetime
import time 
import pandas as pd
from app import create_app, db, login_manager, bcrypt
from models import User, Progress, Test, Universities, QAs, Subject, SubjectCategory, ReviewLessons
from flask import Flask, render_template, request, jsonify


class ReviewChatbot:
    def __init__(self, subject_id, chapter):
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key)
        self.subject_id = subject_id
        self.chapter = chapter

    def return_lesson_content(self):
        data = ReviewLessons.query.filter_by(subject_id=self.subject_id, chapter=self.chapter).first()
        return data.content
    
    def return_message(self, message):
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Bạn là 1 gia sư giải thích lý thuyết bài học cho học sinh, sau đây là phần lý thuyết của bài học học sinh chuẩn bị hỏi: {self.return_lesson_content()} "},
                    {"role": "user", "content": message}
                ]
            )
        if completion.choices[0].message!=None:
            content = completion.choices[0].message.content
            return jsonify({"response": content})
        else :
            return 'Failed to Generate response!'
