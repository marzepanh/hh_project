import subprocess
import sys
import os
import time
import webbrowser
import requests

def check_docker():
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"📦 Проверка Docker...\n{result.stdout.strip()}")
        else:
            print("❌ Docker не найден.")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Docker не установлен или не найден в PATH.")
        sys.exit(1)

def start_docker_compose():
    print("🚀 Запуск Elasticsearch и Kibana через docker-compose...")
    result = subprocess.run(["docker-compose", "up", "-d"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Контейнеры запущены.")
    else:
        print("❗ Ошибка запуска контейнеров:")
        print(result.stderr)
        sys.exit(1)

def wait_for_elasticsearch(timeout=120):
    print("⏳ Ожидание запуска Elasticsearch...")
    for i in range(timeout):
        try:
            response = requests.get("http://localhost:9200")
            if response.status_code == 200:
                print(f"✅ Elasticsearch доступен (после {i+1} сек.)")
                return
        except requests.ConnectionError:
            pass
        print(f"  ⌛ {i+1} сек...", end='\r')
        time.sleep(1)
    print("❌ Elasticsearch не запущен за отведённое время.")
    sys.exit(1)

def open_in_browser():
    print("🌐 Открытие интерфейсов в браузере...")
    webbrowser.open("http://localhost:9200")
    webbrowser.open("http://localhost:5601")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    check_docker()
    start_docker_compose()
    wait_for_elasticsearch()
    open_in_browser()
