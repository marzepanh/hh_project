import requests
import json
import time
from datetime import datetime, timedelta
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys
from dotenv import load_dotenv

# --- Константы ---
vacancies_url = "https://api.hh.ru/vacancies/"
roles_url = "https://api.hh.ru/professional_roles"
token_url = "https://hh.ru/oauth/token"

# --- Авторизация ---
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("CLIENT_ID или CLIENT_SECRET не найдены в .env")
TOKEN_FILE = "token.json"

ACCESS_TOKEN = None
REFRESH_TOKEN = None
TOKEN_EXPIRES_AT = None

# --- Параметры ---
MAX_RETRIES = 5
RETRY_DELAY = 2
REQUEST_DELAY = 0.2
THREADS = 10

# --- Глобальные флаги ---
stop_requested = False

# --- Обработчик завершения ---
def handle_exit(signum, frame):
    global stop_requested
    print("\n⛔ Получен сигнал завершения. Завершаем выполнение корректно...")
    stop_requested = True

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# --- Авторизация ---
def save_token(data):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_token():
    global ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRES_AT
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            ACCESS_TOKEN = data["access_token"]
            REFRESH_TOKEN = data["refresh_token"]
            timestamp = data["timestamp"]
            expires_in = data["expires_in"]
            TOKEN_EXPIRES_AT = datetime.fromtimestamp(timestamp) + timedelta(seconds=expires_in)

def refresh_token():
    global ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRES_AT
    print("🔄 Обновляем токен...")
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        token_data["timestamp"] = time.time()
        save_token(token_data)
        load_token()
        print("✅ Токен обновлен.")
    else:
        print(f"❗ Ошибка при обновлении токена: {response.status_code}")
        print(response.text)
        raise Exception("Ошибка обновления токена")

def ensure_token():
    load_token()
    if not ACCESS_TOKEN or datetime.now() >= TOKEN_EXPIRES_AT:
        refresh_token()

# --- Роли ---
def get_allowed_roles_from_category(category_id="11"):
    try:
        response = requests.get(roles_url)
        if response.status_code == 200:
            data = response.json()
            for category in data['categories']:
                if category['id'] == category_id:
                    return {str(role['id']) for role in category['roles']}
        print("❌ Не удалось получить роли категории.")
    except Exception as e:
        print(f"❗ Ошибка при получении ролей: {e}")
    return set()

allowed_role_ids = get_allowed_roles_from_category()

# --- Проверки ---
def is_2024_vacancy(vacancy_data):
    published_at = vacancy_data.get("published_at")
    if published_at:
        published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%S%z")
        return published_date.year == 2024
    return False

def is_matching_role(vacancy_data):
    roles = vacancy_data.get("professional_roles", [])
    for role in roles:
        if str(role['id']) in allowed_role_ids:
            return True
    return False

# --- Безопасный запрос ---
def safe_request(url):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                print("⚡ 429 Too Many Requests — ждём дольше")
                time.sleep(RETRY_DELAY * 2)
            elif response.status_code == 403:
                print("🚫 403 Forbidden — ждём дольше")
                time.sleep(RETRY_DELAY * 2)
            elif response.status_code == 404:
                return None
            else:
                print(f"❗ Ошибка {response.status_code}")
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            print(f"❗ Ошибка сети: {e}")
            time.sleep(RETRY_DELAY)
        retries += 1
    return None

# --- Работа с файлами ---
def save_processed_ids(processed_ids, filename="processed_vacancy_ids.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(list(processed_ids), f, ensure_ascii=False)

def load_processed_ids(filename="processed_vacancy_ids.json"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

# --- Обработка вакансии ---
def process_vacancy(vacancy_id, idx, total):
    if stop_requested:
        return None, vacancy_id, "stopped"

    ensure_token()
    print(f"🔍 Обработка {idx}/{total}: ID {vacancy_id}")
    response = safe_request(f"{vacancies_url}{vacancy_id}")
    if response is None:
        return None, vacancy_id, "not_found"

    data = response.json()
    published_at = data.get("published_at", "N/A")

    if not is_2024_vacancy(data):
        print(f"⏩ Пропущена (не 2024): ID {vacancy_id}, published_at: {published_at}")
        return None, vacancy_id, "not_2024"

    if not is_matching_role(data):
        print(f"⏩ Пропущена (не та роль): ID {vacancy_id}, published_at: {published_at}")
        return None, vacancy_id, "wrong_role"

    data.pop("branded_description", None)
    return data, vacancy_id, "ok"

# --- Основная функция ---
def fetch_vacancies_by_ids(vacancy_ids):
    output_file = "vacancies_2024.jsonl"
    processed_ids = load_processed_ids()
    to_process = [vid for vid in vacancy_ids if vid not in processed_ids]

    loaded = 0
    skipped = 0
    total = len(to_process)

    with open(output_file, "a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = {executor.submit(process_vacancy, vid, idx+1, total): vid for idx, vid in enumerate(to_process)}

            try:
                for future in as_completed(futures):
                    if stop_requested:
                        break

                    result, vid, status = future.result()
                    processed_ids.add(vid)

                    if status == "ok" and result is not None:
                        f.write(json.dumps(result, ensure_ascii=False) + "\n")
                        loaded += 1
                        if loaded % 50 == 0:
                            print(f"📥 Загружено {loaded} вакансий")
                    elif status != "stopped":
                        skipped += 1

                    save_processed_ids(processed_ids)

            except KeyboardInterrupt:
                print("⛔ Прерывание пользователем. Сохраняем прогресс...")

    save_processed_ids(processed_ids)
    print(f"✅ Всего: {total}, Загружено: {loaded}, Пропущено: {skipped}")

# --- Генерация ID ---
def generate_vacancy_ids_for_2024():
    return [str(i) for i in range(90000000, 120000000)]

# --- Запуск ---
if __name__ == "__main__":
    vacancy_ids = generate_vacancy_ids_for_2024()
    fetch_vacancies_by_ids(vacancy_ids)
