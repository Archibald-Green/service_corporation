from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "D:/diploma/bots/services/service/portal_app/creds/handy-woodland-452812-u0-d7eb0d4eb68d.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_drive_files(page_size=10):
    """
    Возвращает список файлов (name, id, mimeType, webViewLink, webContentLink).
    webViewLink — ссылка для просмотра (Google Docs, Sheets).
    webContentLink — ссылка для скачивания (для обычных файлов).
    """
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)

    results = service.files().list(
        pageSize=page_size,
        # Запрашиваем дополнительные поля
        fields="files(id, name, mimeType, webViewLink, webContentLink)"
    ).execute()

    files = results.get('files', [])
    return files
