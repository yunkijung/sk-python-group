from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from docx import Document
from docx2pdf import convert
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.slack import send_to_slack, send_to_slack_with_file, send_to_slack_for_xlsx
from utils.email import send_certificate_email, send_notification_email
import pandas as pd
from werkzeug.utils import secure_filename
import ftplib

load_dotenv()

SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
FTP_ID = os.getenv("FTP_ID")
FTP_PW = os.getenv("FTP_PW")
FTP_HOST = os.getenv("FTP_HOST")
app = Flask(__name__)
app.secret_key = os.urandom(24)

client = MongoClient('mongodb://localhost:27017/')
db = client['certificate_db']

users_collection = db['users']
login_logs_collection = db['login_logs']
certificate_requests_collection = db['certificate_request_logs']



ALLOWED_EXTENSIONS = {'xlsx'}

UPLOAD_FOLDER = 'uploads'
CERTIFICATE_FOLDER = 'certificates'
CERTIFICATE_PDF_FOLDER = 'certificates_pdf'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



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
    send_certificate_email(user['email'], user['name'], pdf_path)

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
            "password": str(request.form['password']),
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

        send_notification_email(user_data['email'], user_data['name'])
        return redirect(url_for('admin_get'))

    return render_template('add_user.html')


@app.route('/delete_user', methods=['GET'])
def delete_user():

    user_db_id = request.args.get('user_db_id')
    
    if user_db_id:

        try:
            user_id = ObjectId(user_db_id)
        except Exception as e:
            return f"Invalid user_db_id format: {e}", 400
        

        result = users_collection.delete_one({'_id': user_id})
        
        if result.deleted_count == 1:
            return redirect(url_for('admin_get'))
        else:
            return "User not found or deletion failed", 404
    else:
        return "user_db_id is required", 400


@app.route('/user_logs', methods=['GET'])
def user_logs():
    
    user_db_id = request.args.get('user_db_id')
    
    if not user_db_id:
        return "user_db_id is required", 400
    

    try:
        user_id = user_db_id
    except Exception as e:
        return f"Invalid user_db_id format: {e}", 400
    

    login_logs = login_logs_collection.find({'user_db_id': user_id})

    login_logs_list = list(login_logs)

    request_logs = certificate_requests_collection.find({'user_db_id': user_id})
    request_logs_list = list(request_logs)

    return render_template('user_logs.html', login_logs=login_logs_list, certificate_logs=request_logs_list)


@app.route('/upload_xlsx', methods=['POST'])
def upload_xlsx():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            df = pd.read_excel(file_path)

            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            df = df.dropna(subset=['start_date', 'end_date'])
        
            data = []
            for _, row in df.iterrows():
                
                document = {
                    "user_id": row['user_id'],
                    "password": str(row['password']), 
                    "name": row['name'],
                    "email": row['email'],
                    "course": row['course'],
                    "startDate": row['start_date'], 
                    "endDate": row['end_date'],      
                    "role": row['role']
                }
                
                data.append(document)

            users_collection.insert_many(data)

            for student in data:
                send_notification_email(student['email'], student['name'])

            send_to_slack_for_xlsx(SLACK_CHANNEL, file_path)

            hostname = FTP_HOST
            ftp = ftplib.FTP(hostname)
            ftp.login(FTP_ID, FTP_PW)

            with open(file_path, 'rb') as f:
                ftp.storbinary('STOR ' + filename, f)

            return jsonify({"message": "File successfully uploaded and data inserted into MongoDB"}), 200

        except Exception as e:
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500

    return jsonify({"error": "Invalid file format. Only .xlsx allowed."}), 400


@app.route('/ftp', methods=['GET'])
def ftp_get():
    hostname = FTP_HOST  # Your FTP host (IP or domain)
    ftp = ftplib.FTP(hostname)
    ftp.login(FTP_ID, FTP_PW)

    # List to store the processed file information
    file_list = []

    # Callback function to capture the lines of 'LIST' command
    def handle_line(line):
        # Split the line into parts (based on a UNIX-style 'ls -l' listing)
        parts = line.split()
        if len(parts) >= 9:
            file_type = 'Directory' if parts[0].startswith('d') else 'File'
            file_name = parts[8]  # File name is typically the 9th element
            file_size = parts[4]  # File size is typically the 5th element

            # Append a dictionary of processed data
            file_list.append({
                'type': file_type,
                'name': file_name,
                'size': file_size
            })

    # Retrieve the list of files from FTP using the 'LIST' command
    ftp.retrlines('LIST', handle_line)

    # Close FTP connection
    ftp.quit()

    # Render the template with the processed file_list
    return render_template("ftp.html", file_list=file_list)

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(CERTIFICATE_FOLDER):
        os.makedirs(CERTIFICATE_FOLDER)
    if not os.path.exists(CERTIFICATE_PDF_FOLDER):
        os.makedirs(CERTIFICATE_PDF_FOLDER)

    app.run(debug=True)