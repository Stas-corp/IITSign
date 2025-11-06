import logging
from queue import Queue
from pathlib import Path

from src.sign.schema import SignTask
from src.db.dbManager import DatabaseManager
from src.sign.thread_signer import DocumentSigner

logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s %(levelname)s [%(module)s:%(funcName)s] %(message)s',
        handlers=[
            logging.FileHandler('test.log'),  # В файл
            logging.StreamHandler()            # В консоль
        ]
    )     

def test_sign():
    # dbManager = DatabaseManager(
    #         # db_name="test_DB",
    #         is_local_conection=True,
            
    #     )
    
    signer = DocumentSigner(
        1,
        "/app/src/sign/keys/stas.jks",
        True,
        # dbManager,
        "/app/src/sign/keys/Stas.crt"
    )
    que = Queue()
    task = SignTask(
                file_path="/app/data/Projects/Ace_11_09_2025_part1/198321380/0. Позов.pdf",
                key_file_path="/app/src/sign/keys/stas.jks",
                key_password="LALA2108",
                complet_task=que,
                is_sign_Long_type=True,
                output_dir="/app/data/Projects/Ace_11_09_2025_part1/198321380",
                atempts=0
            )
    
    signer.sign_single_file(
        task
    )


def test_create_empty_file():
    path = Path("/app/data/Projects/Ace_11_09_2025_part1/198321380/Україньська.txt")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)  # создаём директорию при необходимости
        with open(path, "w", encoding="utf-8") as f:
            pass  # создаём пустой файл
        print(f"Файл успешно создан: {str(path)}")
    except Exception as e:
        print(f"Ошибка при создании файла {str(path)}: {e}")