from flask import Flask, render_template, request, send_file
from docx import Document
from docx2pdf import convert
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient

app = Flask(__name__)


client = MongoClient('mongodb://localhost:27017/')
db = client['certificate_db']
collection = db['users']
collection = db['login_logs']
collection = db['certificate_requests']

@app.route('/', methods=['GET'])
def certificate():
    # 로그인 페이지로 이동
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def certificate():
    # 사용자 ID, PASSWORD DB 데이터에서 확인

    # DB에 로그인 한 사용자 log 남김

    # Slack으로 사용자 로그인 알림

    # certificate_request.html 반환 (사용자 ID 전달)
    return render_template("certificate_request.html")

@app.route('/certificate', methods=['GET'])
def certificate():
    # 사용자 ID를 가지고 데이터베이스에서 사용자 정보 조회

    # 조회해온 데이터로 doc 파일 변환

    # 변환 한 파일 certificates 폴더에 저장

    # 저장 한 파일 사용자 이메일로 전송

    # DB의 certificate_requests에 요청한 기록 남김

    # Slack으로 사용자가 증명서 요청한 것 알림

    # 사용자에게 파일 다운로드 보냄

    return send_file(pdf_filename, as_attachment=True)


@app.route('/admin', methods=['GET'])
def certificate():

    # 모든 사용자 리스트 데이터 가져옴

    return render_template("admin.html")




if __name__ == "__main__":
    app.run(debug=True)