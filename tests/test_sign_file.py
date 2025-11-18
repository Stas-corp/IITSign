import logging
import platform
from pathlib import Path

from src.sign.model import SignTask, SignerConfig
from src.db.dbManager import DatabaseManager
from src.sign.thread_signer import SignatureService

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
    #         is_conteiner=True
    #     )
    
    if platform.system() == "Windows":
        key = r"C:\Users\ssamo\Documents\Projects\IITSign\src\sign\keys\stas.jks"
        target_path = r"C:\Users\ssamo\Documents"
    elif platform.system() == "Linux":
        key = "/app/src/sign/keys/stas.jks"
        target_path = r"/app/data"
    
    signer_config = SignerConfig(
        key_file_path=key,
        # cert_file_path="/app/src/sign/keys/Stas.crt",
        is_sign_long_type=True,
        max_attempts=1,
        retry_delay=10
        )
    
    signer = SignatureService(signer_config)
    
    task = SignTask(
        file_path=target_path+"/Projects/Ace_11_09_2025_part1/198321380/0. Позов.pdf",
        key_password="LALA2108",
        output_dir=target_path+"/Projects/Ace_11_09_2025_part1/198321380",
    )
    
    signer.sign_file(
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