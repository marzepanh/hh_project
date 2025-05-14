import requests
import time
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# === OAuth конфигурация ===
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("CLIENT_ID или CLIENT_SECRET не найдены в .env")
TOKEN_FILE = "token.json"

# === HH API ===
VACANCIES_URL = "https://api.hh.ru/vacancies"

# === Загрузка и сохранение токенов ===
def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_tokens(tokens):
    tokens['timestamp'] = int(time.time())
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

def is_token_expired(tokens):
    return int(time.time()) >= (tokens['timestamp'] + tokens['expires_in'] - 60)  # -60 сек запаса

def refresh_access_token(refresh_token):
    url = "https://hh.ru/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        new_tokens = response.json()
        save_tokens(new_tokens)
        return new_tokens
    else:
        raise Exception(f"Не удалось обновить токен: {response.status_code} {response.text}")

# === Получение актуального токена ===
def get_valid_access_token():
    tokens = load_tokens()
    if not tokens:
        raise Exception("Токены не найдены. Авторизуйтесь через браузер и сохраните access/refresh токены.")
    if is_token_expired(tokens):
        print("🔄 Токен просрочен, обновляем...")
        tokens = refresh_access_token(tokens['refresh_token'])
    return tokens['access_token']

# === Загрузка вакансий за месяц ===
def fetch_vacancies_for_month(month_start: str, month_end: str, output_file="vacancies_month.jsonl"):
    access_token = get_valid_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "date_from": month_start,
        "date_to": month_end,
        "per_page": 100,
        "page": 0
    }

    with open(output_file, "a", encoding="utf-8") as f:
        while True:
            print(f"📄 Загружаем страницу {params['page']}...")
            resp = requests.get(VACANCIES_URL, headers=headers, params=params)
            if resp.status_code != 200:
                print(f"❌ Ошибка {resp.status_code}: {resp.text}")
                break

            data = resp.json()
            items = data.get("items", [])
            if not items:
                print("✅ Нет больше вакансий.")
                break

            for vacancy in items:
                f.write(json.dumps(vacancy, ensure_ascii=False) + "\n")

            params['page'] += 1
            time.sleep(0.4)

    print(f"📥 Загрузка завершена. Файл: {output_file}")

# === Пример запуска ===
if __name__ == "__main__":
    # Задаем нужный месяц
    fetch_vacancies_for_month("2024-04-01T00:00:00", "2024-04-30T23:59:59")
