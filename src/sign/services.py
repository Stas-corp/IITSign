import time
import logging
from pathlib import Path
from typing import Callable, Union, Optional

from src.sign.thread_signer import BatchSigner

def sign_folder_documents(
    root_folder: str,
    key_file: Union[str, Path],
    key_password: str,
    is_long_sign: bool = True,
    workers: int = 10,
    cert_file: Optional[Union[str, Path]] = None,
    extensions: Optional[list[str]] = None,
    output_base_dir: Optional[Union[str, Path]] = None,
    callback_progress: Optional[Callable[[int, int, str], None]] = None,
    max_attempts: int = 3,
    retry_delay: int = 10
) -> tuple[bool, str]:
    """
    Выполнить пакетную подпись документов
    
    Args:
        root_folder: Папка с документами для подписи
        key_file: Путь к файлу ключа
        key_password: Пароль для ключа
        is_long_sign: Использовать CAdES-X Long формат
        workers: Количество рабочих потоков
        cert_file: Путь к файлу сертификата (опционально)
        extensions: Список расширений файлов для подписи
        output_base_dir: Директория для сохранения подписанных файлов
        callback_progress: Callback для отслеживания прогресса (completed, total)
        max_attempts: Максимальное количество попыток подписи
        retry_delay: Задержка между попытками в секундах
    
    Returns:
        Сообщение с результатами подписи
    """
    
    if extensions is None:
        extensions = ['.pdf', '.xml']
    
    try:
        batch_signer = BatchSigner(
            key_file_path=key_file,
            cert_file_path=cert_file,
            is_sign_long_type=is_long_sign,
            max_attempts=max_attempts,
            retry_delay=retry_delay,
            max_workers=workers,
            extensions=extensions
        )
        
        start_time = time.time()
        
        results = batch_signer.sign_documents_batch(
            root_folder=root_folder,
            key_password=key_password,
            output_base_dir=output_base_dir,
            progress_callback=callback_progress
        )
        
        if not results:
            return (False, "No file for sign!")
        
        elapsed_time = time.time() - start_time
        
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        message = f"""
Batch signing completed:

    Successful: {successful}
    
    Failed: {failed}
    
    Total files: {len(results)}
    
    Total time: {elapsed_time:.2f}s
    
    Average time per file: {elapsed_time / len(results):.2f}s
        """.strip()
        
        if failed > 0:
            logging.warning(f"Failed files:")
            for result in results:
                if not result.success:
                    logging.warning(f"  - {result.file_path}: {result.error_message}")
        
        logging.info(message)
        return (True, message)
        
    except Exception as e:
        message = f"Batch signing failed: {e}"
        logging.error(message)
        return (False, message)