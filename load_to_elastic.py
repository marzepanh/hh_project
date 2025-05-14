import json
from elasticsearch import Elasticsearch, helpers
from concurrent.futures import ThreadPoolExecutor, as_completed

# Параметры подключения
ES_HOST = "http://localhost:9200"
ES_INDEX = "vacancies"
BATCH_SIZE = 1000  # Размер батча
MAX_WORKERS = 4    # Количество параллельных потоков

# Инициализация клиента
es = Elasticsearch(ES_HOST)

def recreate_index():
    if es.indices.exists(index=ES_INDEX):
        print(f"🗑️ Удаляем существующий индекс '{ES_INDEX}'...")
        es.indices.delete(index=ES_INDEX)
    
    print(f"✨ Создаем новый индекс '{ES_INDEX}' без явного маппинга...")
    es.indices.create(index=ES_INDEX)
    print(f"✅ Индекс '{ES_INDEX}' успешно создан.")

def send_batch(batch, batch_number):
    helpers.bulk(es, batch)
    print(f"📤 Пакет №{batch_number} отправлен ({len(batch)} документов)")

def load_data_to_elasticsearch_parallel(jsonl_file_path):
    batch = []
    futures = []
    batch_number = 1

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        with open(jsonl_file_path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file, start=1):
                doc = json.loads(line)
                action = {
                    "_index": ES_INDEX,
                    "_id": doc.get("id"),
                    "_source": doc
                }
                batch.append(action)

                if len(batch) >= BATCH_SIZE:
                    future = executor.submit(send_batch, batch.copy(), batch_number)
                    futures.append(future)
                    batch = []
                    batch_number += 1

            # Отправка оставшихся документов
            if batch:
                future = executor.submit(send_batch, batch.copy(), batch_number)
                futures.append(future)

        # Ждем завершения всех задач
        for future in as_completed(futures):
            future.result()

    print(f"✅ Все документы загружены в Elasticsearch параллельно.")

if __name__ == "__main__":
    recreate_index()
    load_data_to_elasticsearch_parallel("full_vacancies_stream.jsonl")
