#  Проект анализа вакансий с HeadHunter

Этот проект предназначен для парсинга вакансий с hh.ru, фильтрации по ролям/датам, сохранения в формате JSONL и загрузки в Elasticsearch для последующего анализа через Kibana.

##  Структура проекта

```markdown
hh_project/
├── docker-compose.yml        # Конфигурация для Elasticsearch и Kibana
├── parser_by_id.py           # Скрипт парсинга по ID
├── parser_by_date.py         # Скрипт парсинга по дате
├── auth_hh.py                # Авторизация и обновление токенов hh.ru
├── load_to_elastic.py       # Загрузка JSONL-файла в Elasticsearch
├── start_services.py        # Автоматический запуск Elasticsearch и Kibana
└── README.md                
```


##  Установка и запуск

### 1. Установите Docker

- [Скачать Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 2. Убедитесь, что Docker работает

```bash
docker --version
```
3. Запустите инфраструктуру
```bash
python start_services.py
```
 При первом запуске образы Elasticsearch и Kibana будут загружены (требуется VPN из РФ).

4. Откроются страницы:
Elasticsearch: http://localhost:9200

Kibana: http://localhost:5601

Использование
Авторизация в hh.ru
Перед парсингом необходимо пройти авторизацию:

```bash
python auth_hh.py
```
После этого будет получён access token и refresh token, которые сохраняются в token.json

Парсинг вакансий
Вы можете собрать вакансии одним из двух способов:

По ID:

```bash
python parser_by_id.py
```
По диапазону дат:

```bash
python parser_by_date.py
```
Результат сохраняется в файл full_vacancies_stream.jsonl.

Загрузка данных в Elasticsearch
После запуска Elasticsearch:

```bash
python load_to_elastic.py
```
Скрипт создаст индекс (если он не существует) и загрузит туда данные из JSONL-файла.

 Дополнительно: запуск через EXE
Вы можете использовать start_services.exe, чтобы:

автоматически запустить Docker-сервисы

открыть браузер с Kibana и Elasticsearch

Вопросы
Если что-то не работает — проверьте VPN и доступ к docker.elastic.co. Также проверьте логи с помощью:

```bash
docker-compose logs -f
```