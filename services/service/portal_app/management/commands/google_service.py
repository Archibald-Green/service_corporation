from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import openpyxl
from openpyxl.utils import get_column_letter
from asgiref.sync import sync_to_async
from fpdf import FPDF
import os

SERVICE_ACCOUNT_FILE = "D:/diploma/bots/services/service/portal_app/creds/handy-woodland-452812-u0-d7eb0d4eb68d.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_drive_files_with_links(page_size=10):
    """
    Возвращает список словарей вида:
    [
      {
        "id": <str>,
        "name": <str>,
        "mimeType": <str>,
        "file_link": <str или None>
      },
      ...
    ]
    
    file_link — лучшая ссылка для открытия/редактирования/скачивания.
    Если файл не расшарен и нет webViewLink/webContentLink, может быть None.
    """
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)

    results = service.files().list(
        pageSize=page_size,
        fields="files(id, name, mimeType, webViewLink, webContentLink)"
    ).execute()

    files = results.get('files', [])

    final_list = []
    for f in files:
        file_id = f.get("id")
        name = f.get("name")
        mime_type = f.get("mimeType")
        web_view = f.get("webViewLink")
        web_content = f.get("webContentLink")

        # Логика определения ссылки
        if web_view:
            # Если есть webViewLink (обычно при расшаренном файле), используем его
            file_link = web_view
        else:
            # Иначе пытаемся сгенерировать вручную
            if mime_type == "application/vnd.google-apps.document":
                # Google Doc
                file_link = f"https://docs.google.com/document/d/{file_id}/edit"
            elif mime_type == "application/vnd.google-apps.spreadsheet":
                # Google Sheet
                file_link = f"https://docs.google.com/spreadsheets/d/{file_id}/edit"
            else:
                # Обычный файл (PDF, ZIP, DOCX, etc.)
                file_link = web_content  # Может быть None, если не расшарен
        final_list.append({
            "id": file_id,
            "name": name,
            "mimeType": mime_type,
            "file_link": file_link
        })

    return final_list
def get_salary_by_iin(iin: str):
    """
    Ищет в Google Sheets (название "Зарплаты") «header row» с ячейками "ИИН", "ФИО", "Зарплата"
    в любой строке. Затем ниже этой строки ищет конкретный iin и возвращает (fio, salary).
    Если не найдено — возвращает None.
    """

    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)
    client = gspread.authorize(creds)

    # Открываем таблицу по названию (например, "Зарплаты")
    sheet = client.open("Зарплаты").sheet1  # если у вас другое имя или лист - измените
    data = sheet.get_all_values()

    if not data:
        print("DEBUG: Пустая таблица.")
        return None

    # Ищем "header row", где присутствуют все нужные заголовки
    needed_headers = ["ИИН", "ФИО", "Зарплата"]

    # Найдём строку (index i), в которой присутствуют все эти слова
    header_row_index = None
    col_map = {}  # dict: заголовок -> col_index

    for i, row in enumerate(data):
        # Проверим, есть ли все нужные заголовки в этой строке
        found_cols = {}
        for header in needed_headers:
            try:
                col_idx = row.index(header)
                found_cols[header] = col_idx
            except ValueError:
                # Этот header не найден в данной строке
                break

        if len(found_cols) == len(needed_headers):
            # Мы нашли строку, где есть все заголовки
            header_row_index = i
            col_map = found_cols
            break

    if header_row_index is None:
        print("DEBUG: Не нашли строку, где есть все заголовки:", needed_headers)
        return None

    print(f"DEBUG: Заголовки найдены в строке {header_row_index+1} (0-based={header_row_index}).")
    print("DEBUG: col_map =", col_map)

    iin_col = col_map["ИИН"]
    fio_col = col_map["ФИО"]
    salary_col = col_map["Зарплата"]

    # Теперь ищем iin ниже header_row_index
    for row_index in range(header_row_index+1, len(data)):
        row = data[row_index]
        # Убедимся, что строка достаточно длинная
        if len(row) <= max(iin_col, fio_col, salary_col):
            continue

        row_iin = row[iin_col].strip()
        if row_iin == iin.strip():
            fio = row[fio_col]
            salary = row[salary_col]
            print(f"DEBUG: Найден iin={iin} в строке {row_index+1}: fio={fio}, salary={salary}")
            return (fio, salary)

    print(f"DEBUG: iin={iin} не найден ниже строки заголовков.")
    return None


def make_short_name_no_dots_for_user(user_obj) -> str:
    """
    Собирает user_obj.name + user_obj.first_name и превращает "Иванов Иван" → "ИвановИ" 
    (убирает точки и пробелы).
    Если одно из полей пустое, возвращает то, что есть.
    """
    surname = (user_obj.name or "").strip()       # Фамилия, например "Иванов"
    fname = (user_obj.first_name or "").strip()     # Имя, например "Иван"
    
    if not surname and not fname:
        return ""  # Нет данных для формирования сокращения

    # Собираем полное имя "Иванов Иван"
    full_name = f"{surname} {fname}".strip()
    # Разбиваем строку по пробелам
    parts = full_name.split()

    if len(parts) < 2:
        # Если одна из частей отсутствует, просто удаляем точки и пробелы
        return full_name.replace(".", "").replace(" ", "")

    # Формируем сокращение: фамилия + первая буква имени, например "ИвановИ"
    short = f"{parts[0]}{parts[1][0]}"
    short = short.replace(".", "").replace(" ", "")
    return short


def get_vacation_by_user_and_job(user_obj, job: str):
    """
    Формирует сокращённое ФИО из user_obj.name + user_obj.first_name, а затем ищет
    в Google Sheets (название "График отпусков") строку, где:
      - Столбец "Ф.И.О." (без точек и пробелов, в нижнем регистре) начинается со сформированного сокращения.
      - Столбец "Должность" (в нижнем регистре) равен job.lower().
    Если совпадение найдено, возвращает словарь с ключами: days, agreed, transfer, note.
    В противном случае возвращает None.
    """
    short_fio = make_short_name_no_dots_for_user(user_obj)

    # Авторизация в Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)
    client = gspread.authorize(creds)

    sheet = client.open("График отпусков").sheet1
    data = sheet.get_all_values()
    if not data:
        return None

    # Определяем требуемые заголовки в нижнем регистре для гибкого сравнения
    required_headers = [
        "ф.и.о.",
        "должность",
        "количество календарных дней",
        "согласованные дни отпуска",
        "перенесение отпуска",
        "примечание"
    ]

    header_row = None
    header_index = None
    # Ищем строку, содержащую все требуемые заголовки
    for i, row in enumerate(data):
        row_clean = [cell.strip().lower() for cell in row]
        print(f"Строка {i}: {row_clean}")
        if all(header in row_clean for header in required_headers):
            header_row = row_clean
            header_index = i
            break

    if not header_row:
        print("Не найдены нужные заголовки в таблице. Доступные строки:")
        for i, row in enumerate(data):
            print(f"Строка {i}: {row}")
        return None

    try:
        fio_col = header_row.index("ф.и.о.")
        job_col = header_row.index("должность")
        days_col = header_row.index("количество календарных дней")
        agreed_col = header_row.index("согласованные дни отпуска")
        transfer_col = header_row.index("перенесение отпуска")
        note_col = header_row.index("примечание")
    except ValueError:
        print("Не найдены нужные заголовки в найденной строке:", header_row)
        return None

    short_fio_lower = short_fio.lower()
    job_lower = job.lower()

    # Проходим по каждой строке, начиная со строки после найденных заголовков
    for row in data[header_index + 1:]:
        if len(row) <= max(fio_col, job_col, days_col, agreed_col, transfer_col, note_col):
            continue

        row_fio = row[fio_col].replace(".", "").replace(" ", "").lower()
        row_job = row[job_col].strip().lower()

        # Используем startswith для гибкого сравнения ФИО
        if row_fio.startswith(short_fio_lower) and row_job == job_lower:
            return {
                "days": row[days_col],
                "agreed": row[agreed_col],
                "transfer": row[transfer_col],
                "note": row[note_col]
            }

    return None



def get_full_name(user_obj) -> str:
    return f"{user_obj.name or ''} {user_obj.first_name or ''}".strip()

def get_payroll_by_user_from_google_sheet(user_obj, month: str = None):
    """
    Ищет расчетный лист пользователя в Google Sheets (Таблица Зарплат).
    Функция самостоятельно находит строку с заголовками (ищет первую строку, где
    хотя бы один заголовок содержит "ийн") и использует её для определения столбца ИИН.
    Если параметр month указан, фильтрует записи по нему.
    Возвращает список словарей (один словарь – одна запись).
    """
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Таблица Зарплат").sheet1
    data = sheet.get_all_values()
    if not data:
        return []
    
    header_row = None
    header_row_index = None
    # Ищем первую строку, в которой хотя бы один элемент содержит "ийн" (без учета регистра)
    for i in range(min(5, len(data))):
        row = data[i]
        # Если хоть один элемент содержит "ийн", считаем эту строку заголовком
        if any("иин" in str(cell).strip().lower() for cell in row):
            header_row = [str(cell).strip() for cell in row]
            header_row_index = i
            break
    if header_row is None:
        print("DEBUG: Заголовок с 'ийн' не найден в первых 5 строках.")
        return []
    
    # Ищем индекс столбца ИИН (ищем точное совпадение или если "ийн" входит в текст)
    iin_idx = None
    for idx, h in enumerate(header_row):
        h_norm = h.replace(" ", "").lower()
        if h_norm == "иин" or "иин" in h_norm:
            iin_idx = idx
            break
    if iin_idx is None:
        print("DEBUG: Столбец с ИИН не найден в заголовке:", header_row)
        return []
    
    # Аналогично ищем столбец для Месяца, если требуется фильтрация
    month_idx = None
    for idx, h in enumerate(header_row):
        if "месяц" in h.lower():
            month_idx = idx
            break
    if month is not None and month_idx is None:
        print("DEBUG: Столбец с Месяцем не найден, фильтрация по месяцу не будет произведена.")
    
    results = []
    user_iin = str(user_obj.iin or "").strip().lower()
    print("DEBUG: ИИН пользователя из БД:", user_iin)
    
    # Используем строки после найденного заголовка
    data_rows = data[header_row_index + 1:]
    for row in data_rows:
        if len(row) < len(header_row):
            continue
        row_norm = [str(cell).strip() for cell in row]
        row_iin = row_norm[iin_idx].lower()
        print("DEBUG: Сравниваем с ИИН из таблицы:", row_iin)
        if row_iin == user_iin:
            if month and month_idx is not None:
                row_month = row_norm[month_idx]
                if row_month != month:
                    continue
            payroll = dict(zip(header_row, row_norm))
            results.append(payroll)
    return results

def format_payroll(payroll: dict) -> str:
    """
    Форматирует словарь с данными расчетного листа в удобный для вывода текст.
    """
    msg = (
        f"ФИО: {payroll.get('ФИО')}\n"
        f"ИИН: {payroll.get('ИИН')}\n"
        f"Табельный номер: {payroll.get('Табельный номер')}\n"
        f"Должность: {payroll.get('Должность')}\n"
        f"Месяц: {payroll.get('Месяц')}\n"
        f"Оклад: {payroll.get('Оклад')}\n"
        f"Премия: {payroll.get('Премия')}\n"
        f"ИПН: {payroll.get('ИПН')}\n"
        f"ОПВ: {payroll.get('ОПВ')}\n"
        f"ОСМС: {payroll.get('ОСМС')}\n"
        f"Удержания: {payroll.get('Удержания')}\n"
        f"Итого к выплате: {payroll.get('Итого к выплате')}"
    )
    return msg

def save_payroll_to_pdf(payroll: dict, output_dir="/mnt/data/payroll_pdfs/") -> str:
    """
    Сохраняет расчетный лист (словарь с данными) в PDF-файл.
    Файл будет сохранён в директории output_dir с именем, сформированным из ФИО и месяца.
    Возвращает полный путь к сохранённому PDF-файлу.
    """
    from fpdf import FPDF
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    employee = payroll.get("ФИО", "unknown").replace(" ", "_")
    month = payroll.get("Месяц", "unknown").replace(" ", "_")
    filename = f"{employee}_{month}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    pdf = FPDF()
    # Добавляем TrueType-шрифт, который поддерживает Unicode. Убедитесь, что файл DejaVuSans.ttf доступен.
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_page()
    pdf.set_font("DejaVu", size=12)
    
    pdf.cell(200, 10, txt="Расчетный лист / Есеп парағы", ln=True, align="C")
    pdf.ln(10)
    
    lines = format_payroll(payroll).split("\n")
    for line in lines:
        pdf.cell(200, 10, txt=line, ln=True)
    
    pdf.output(output_path)
    return output_path