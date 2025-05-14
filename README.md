# 📊 Проект анализа вакансий с HeadHunter

Этот проект предназначен для парсинга вакансий с hh.ru, фильтрации по ролям/датам, сохранения в формате JSONL и загрузки в Elasticsearch для последующего анализа через Kibana.

## 🗂️ Структура проекта

hh_project/
├── docker-compose.yml/ # Конфигурация для Elasticsearch и Kibana
├── parser_by_id.py # Скрипт парсинга по ID
├── parser_by_date.py # Скрипт парсинга по дате
├── auth_hh.py # Авторизация и обновление токенов hh.ru
├── load_to_elastic.py # Загрузка JSONL-файла в Elasticsearch
├── full_vacancies_stream.jsonl # Файл с сохранёнными вакансиями
├── start_services.py # Автоматический запуск Elasticsearch и Kibana
├── README.md # Этот файл


## ⚙️ Установка и запуск

### 1. Установите Docker

- [Скачать Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 2. Убедитесь, что Docker работает

```bash
docker --version
3. Запустите инфраструктуру
bash
python start_services.py
🔐 При первом запуске образы Elasticsearch и Kibana будут загружены (требуется VPN из РФ).

4. Откроются страницы:
Elasticsearch: http://localhost:9200

Kibana: http://localhost:5601

5. Парсинг вакансий
По ID:

bash
python parser_by_id.py
По дате:

bash
python parser_by_date.py
6. Загрузка в Elasticsearch
bash
python load_to_elastic.py
📁 Что НЕ включается в репозиторий
🔒 Файл token.json с авторизацией

📦 Папки elastic, kibana — без скачанных образов

🐘 Данные Elasticsearch

🛑 Логи

🪄 Дополнительно: запуск через EXE
Вы можете использовать start_services.exe, чтобы:

автоматически запустить Docker-сервисы

открыть браузер с Kibana и Elasticsearch

📞 Вопросы
Если что-то не работает — проверьте VPN и доступ к docker.elastic.co. Также проверьте логи с помощью:

bash
docker-compose logs -f