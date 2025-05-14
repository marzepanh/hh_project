import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import os
import time
from dotenv import load_dotenv

# 🔐 Данные клиента
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    raise ValueError("CLIENT_ID, CLIENT_SECRET или REDIRECT_URI не найдены в .env")


TOKEN_FILE = "token.json"

# 🌍 Авторизация
def open_auth_url():
    auth_url = (
        "https://hh.ru/oauth/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    print("🌐 Открываем браузер для авторизации...")
    webbrowser.open(auth_url)

# 🌐 HTTP сервер для перехвата кода
class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        code = params.get("code", [None])[0]
        if code:
            self.server.auth_code = code
            self.send_response(200)
            self.end_headers()
            self.wfile.write("✅ Авторизация завершена. Можете закрыть окно.")
            print(f"🔐 Код авторизации получен: {code}")

def get_auth_code():
    server = HTTPServer(("localhost", 8080), OAuthHandler)
    server.handle_request()
    return server.auth_code

# 🔁 Обмен кода на токен
def exchange_code_for_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    }
    response = requests.post("https://hh.ru/oauth/token", data=data)
    if response.status_code == 200:
        tokens = response.json()
        tokens["timestamp"] = time.time()
        save_tokens(tokens)
        return tokens
    else:
        print("❌ Ошибка получения токена:", response.status_code, response.text)
        return None

# 💾 Сохранение токена
def save_tokens(tokens):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)

# 📂 Загрузка токена
def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# ⏳ Проверка истечения токена
def is_token_expired(tokens):
    return time.time() > tokens["timestamp"] + tokens.get("expires_in", 3600) - 60

# 🔁 Обновление токена по refresh_token
def refresh_access_token(refresh_token):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post("https://hh.ru/oauth/token", data=data)
    if response.status_code == 200:
        tokens = response.json()
        tokens["timestamp"] = time.time()
        save_tokens(tokens)
        print("🔁 Access token успешно обновлён.")
        return tokens
    else:
        print("❌ Ошибка обновления токена:", response.status_code, response.text)
        return None

# 🧪 Тест запроса
def test_api(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.hh.ru/me", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"👤 Вы вошли как {user.get('first_name')} {user.get('last_name')}")
    else:
        print("❌ Ошибка при запросе к API:", response.status_code, response.text)

# ▶️ Основной поток
def main():
    tokens = load_tokens()
    if tokens:
        if is_token_expired(tokens):
            print("🔄 Access token устарел. Обновляем...")
            tokens = refresh_access_token(tokens["refresh_token"])
    else:
        open_auth_url()
        code = get_auth_code()
        tokens = exchange_code_for_token(code)

    if tokens:
        test_api(tokens["access_token"])

if __name__ == "__main__":
    main()
