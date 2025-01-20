from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from docx import Document
from docx2pdf import convert
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.slack import send_to_slack, send_to_slack_with_file
from utils.email import send_certificate_email


load_dotenv()

SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
REC_EMAIL = os.getenv("REC_EMAIL")

app = Flask(__name__)
app.secret_key = os.urandom(24)

client = MongoClient('mongodb://localhost:27017/')
db = client['certificate_db']

users_collection = db['users']
login_logs_collection = db['login_logs']
certificate_requests_collection = db['certificate_request_logs']



@app.route('/', methods=['GET'])
def home_get():
    # 로그인 페이지로 이동
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login_post():

    user_id = request.form.get('user_id')
    pw = request.form.get('pw')

    # 사용자 ID, PASSWORD DB 데이터에서 확인
    user = users_collection.find_one({"user_id": user_id, "password": pw})
    
    if user:
        # DB에 로그인 한 사용자 log 남김
        login_log = {
            "user_db_id": str(user["_id"]),  # Store the ObjectId as a string if needed
            "login_time": datetime.now()
        }
        login_logs_collection.insert_one(login_log)

        print(user["_id"])

        # Slack으로 사용자 로그인 알림
        send_to_slack(SLACK_CHANNEL, user['user_id'])

        # certificate_request.html 반환 (사용자 ID 전달)
        if user["role"] == "admin":
            return redirect(url_for('admin_get'))
        else:
            current_date = datetime.now().strftime('%Y-%m-%d')
            return render_template("certificate_request.html", user_info=user, user_db_id=str(user["_id"]), current_date=current_date)


    else:
        flash('Invalid username or password.', 'error')
        return redirect(url_for('home_get'))


@app.route('/certificate', methods=['GET'])
def certificate_get():
    # 사용자 ID를 가지고 데이터베이스에서 사용자 정보 조회
    user_db_id = request.args.get('user_db_id')
    
    if not user_db_id:
        flash('User ID is missing.', 'error')
        return redirect(url_for('home_get'))
    
    user = users_collection.find_one({"_id": ObjectId(user_db_id)})
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('home_get'))
    

    # 조회해온 데이터로 doc 파일 변환
    template_path = 'doc_templates/certificate_template.docx'  # Path to your DOCX template
    doc = Document(template_path)
    current_date = datetime.now().strftime('%Y-%m-%d')

    for para in doc.paragraphs:
        if 'COURSE' in para.text:
            para.text = para.text.replace('COURSE', user['course'])
        if 'NAME' in para.text:
            para.text = para.text.replace('NAME', user['name'])
        if 'CUR_DATE' in para.text:
            para.text = para.text.replace('CUR_DATE', current_date)
        if 'EDU_DATE' in para.text:
            para.text = para.text.replace('EDU_DATE', f"{user['startDate']} - {user['endDate']}")
        if 'FIN_DATE' in para.text:
            para.text = para.text.replace('FIN_DATE', user['endDate'])

    

    # 변환 한 파일 certificates, certificates_pdf 폴더에 저장
    modified_doc_path = f"certificates/{user['name']}_certificate_{current_date}.docx"
    doc.save(modified_doc_path)

    # DOCX to PDF
    pdf_path = f"certificates_pdf/{user['name']}_certificate_{current_date}.pdf"
    convert(modified_doc_path, pdf_path)


    # DB의 certificate_requests에 요청한 기록 남김
    certificate_request = {
        "user_db_id": str(user["_id"]),
        "user_name": user['name'],
        "request_time": datetime.now()
    }
    certificate_requests_collection.insert_one(certificate_request)

    # 저장 한 파일 사용자 이메일로 전송
    send_certificate_email(REC_EMAIL, user['name'], pdf_path)

    # Slack으로 사용자가 증명서 요청한 것 알림
    send_to_slack_with_file(SLACK_CHANNEL, pdf_path, user['name'], user['email'])

    # 사용자에게 파일 다운로드 보냄
    return send_file(pdf_path, as_attachment=True)



@app.route('/admin', methods=['GET'])
def admin_get():
    # 관리자를 제외한 모든 사용자 리스트 조회해서 보냄
    users = users_collection.find({"role": {"$ne": "admin"}})

    users_list = list(users)

    return render_template("admin.html", users=users_list)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        # 입력값 가져오기
        user_data = {
            "user_id": request.form['user_id'],
            "password": request.form['password'],
            "name": request.form['name'],
            "email": request.form['email'],
            "course": request.form['course'],
            "startDate": request.form['start_date'],
            "endDate": request.form['end_date'],
            "role": request.form['role']
        }

        # 사용자 데이터 DB에 삽입
        users_collection.insert_one(user_data)
        flash('사용자가 성공적으로 추가되었습니다.', 'success')
        return redirect(url_for('admin_get'))

    return render_template('add_user.html')

if __name__ == "__main__":
    app.run(debug=True)