import smtplib  # SMTP 프로토콜을 사용하여 이메일을 전송하기 위한 라이브러리
from email.mime.text import MIMEText  # 이메일 본문을 작성하기 위한 MIME 형식 지원
from email.mime.multipart import MIMEMultipart  # 여러 MIME 파트를 포함하는 이메일 작성
from email.mime.application import MIMEApplication  # 파일 첨부를 위한 MIME 형식 지원
import os  # 환경 변수와 파일 경로 처리를 위한 라이브러리 

from dotenv import load_dotenv
load_dotenv()

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_notification_email(recipient_email, recipient_name):

    EMAIL_ID = os.getenv("EMAIL_ID")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    # 계정 정보가 설정되지 않은 경우 예외 발생
    if not EMAIL_ID or not EMAIL_PASS:
        raise ValueError("이메일 계정 정보(EMAIL_ID, EMAIL_PASS)가 설정되지 않았습니다.")

    # SMTP 서버 정보 설정
    smtp_server = 'smtp.naver.com'  # Naver 메일 서버 주소
    smtp_port = 587  # SMTP 서버 포트 (TLS를 사용하는 기본 포트)

    # 이메일 메시지 생성
    msg = MIMEMultipart()  # 이메일 메시지의 컨테이너 생성
    msg['From'] = EMAIL_ID  # 발신자 이메일 주소
    msg['To'] = recipient_email  # 수신자 이메일 주소
    msg['Subject'] = f"[계정 생성 알림] {recipient_name}님, 계정이 생성되었습니다!"  # 이메일 제목

    # 이메일 본문 작성
    body = f"""
    안녕하세요, {recipient_name}님!

    귀하의 수료증 발급 계정이 생성되었습니다.
    www.example.comm 에서 수료증을 확인하실 수 있습니다.

    감사합니다.
    """
    msg.attach(MIMEText(body, 'plain'))  # 본문을 평문으로 첨부

    # SMTP 서버를 통해 이메일 전송
    try:
        # SMTP 서버 연결
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()  # TLS(보안 연결) 시작
            smtp.login(EMAIL_ID, EMAIL_PASS)  # SMTP 서버에 로그인
            # 이메일 발송
            smtp.sendmail(EMAIL_ID, recipient_email, msg.as_string())
            print(f"알림이 {recipient_email}로 성공적으로 발송되었습니다.")  # 성공 메시지 출력
    except Exception as e:
        # 이메일 전송 중 오류 발생 시 예외 처리
        print(f"이메일 발송 중 오류 발생: {e}")




def send_certificate_email(recipient_email, recipient_name, pdf_path):
    """
    수료증 PDF를 이메일로 전송하는 함수.

    Parameters:
        recipient_email (str): 수신자의 이메일 주소
        recipient_name (str): 수신자의 이름
        pdf_path (str): 첨부할 PDF 파일의 경로
    """

    # 환경 변수에서 이메일 계정 정보 가져오기
    # EMAIL_ID: 발신 이메일 계정 ID
    # EMAIL_PASS: 발신 이메일 계정 비밀번호
    EMAIL_ID = os.getenv("EMAIL_ID")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    # 계정 정보가 설정되지 않은 경우 예외 발생
    if not EMAIL_ID or not EMAIL_PASS:
        raise ValueError("이메일 계정 정보(EMAIL_ID, EMAIL_PASS)가 설정되지 않았습니다.")

    # SMTP 서버 정보 설정
    smtp_server = 'smtp.naver.com'  # Naver 메일 서버 주소
    smtp_port = 587  # SMTP 서버 포트 (TLS를 사용하는 기본 포트)

    # 이메일 메시지 생성
    msg = MIMEMultipart()  # 이메일 메시지의 컨테이너 생성
    msg['From'] = EMAIL_ID  # 발신자 이메일 주소
    msg['To'] = recipient_email  # 수신자 이메일 주소
    msg['Subject'] = f"[수료증 발급] {recipient_name}님, 축하드립니다!"  # 이메일 제목

    # 이메일 본문 작성
    body = f"""
    안녕하세요, {recipient_name}님!

    축하드립니다! 귀하의 수료증이 발급되었습니다.
    첨부된 PDF 파일에서 수료증을 확인하실 수 있습니다.

    감사합니다.
    """
    msg.attach(MIMEText(body, 'plain'))  # 본문을 평문으로 첨부

    # PDF 파일 첨부
    with open(pdf_path, 'rb') as pdf_file:
        # 첨부할 파일을 읽고 MIMEApplication 객체 생성
        attachment = MIMEApplication(pdf_file.read(), _subtype="pdf")
        # 첨부 파일에 Content-Disposition 헤더 추가
        attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=os.path.basename(pdf_path)  # 파일 이름 설정
        )
        msg.attach(attachment)  # 이메일 메시지에 첨부 파일 추가

    # SMTP 서버를 통해 이메일 전송
    try:
        # SMTP 서버 연결
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()  # TLS(보안 연결) 시작
            smtp.login(EMAIL_ID, EMAIL_PASS)  # SMTP 서버에 로그인
            # 이메일 발송
            smtp.sendmail(EMAIL_ID, recipient_email, msg.as_string())
            print(f"수료증이 {recipient_email}로 성공적으로 발송되었습니다.")  # 성공 메시지 출력
    except Exception as e:
        # 이메일 전송 중 오류 발생 시 예외 처리
        print(f"이메일 발송 중 오류 발생: {e}")