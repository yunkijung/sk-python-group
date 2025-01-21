from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import dotenv, os


dotenv.load_dotenv()
# Slack API 토큰과 메시지를 보낼 채널 설정
SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
# 채널 접근 후 URL 뒤에서 확인 가능

def send_to_slack_for_xlsx(channel, file_path):
    # WebClient 인스턴스 생성
    client = WebClient(token=SLACK_API_TOKEN)
    
    message = f"😊  {file_path}가 업로드 되었습니다."

    try:
        response = client.files_upload_v2(
            channel=channel, 
            file=file_path,
            initial_comment=message
        )
        # 업로드 성공 메시지 출력
        print("File uploaded successfully:", response["file"]["name"])
    
    except SlackApiError as e:
        # 에러 처리
        print("Error sending/uploading message:", e.response["error"])

def send_to_slack_with_file(channel, file_path, name, email):
    # WebClient 인스턴스 생성
    client = WebClient(token=SLACK_API_TOKEN)
    
    message = f"😊  {name}님의 수료증을 이메일로 전송 완료했습니다!\n- 이메일 주소: {email})"

    try:
        response = client.files_upload_v2(
            channel=channel, 
            file=file_path,
            initial_comment=message
        )
        # 업로드 성공 메시지 출력
        print("File uploaded successfully:", response["file"]["name"])
    
    except SlackApiError as e:
        # 에러 처리
        print("Error sending/uploading message:", e.response["error"])


def send_to_slack(channel, user_id):
    # WebClient 인스턴스 생성
    client = WebClient(token=SLACK_API_TOKEN)


    try:
        response = client.chat_postMessage(
            channel=channel,
            text=f"User {user_id} logged in at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # 응답 출력
        print("Message sent successfully: ", response["message"]["text"])
    
    except SlackApiError as e:
        # 에러 처리
        print("Error sending/uploading message:", e.response["error"])

