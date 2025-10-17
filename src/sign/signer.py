import time
import logging
from pathlib import Path
from typing import Callable, Union

from src.sign.thread_signer import BatchSigner

def main(
    root_folder: str,
    key_file: str,
    
    key_password: str, 
    workers: int = 10,
    cert_file: Union[str, Path] = None,
    callback_progress: Callable = None
):   
    batch_signer = BatchSigner(
        cert_file_path=cert_file,
        max_workers=workers
    )
    start_time = time.time()
    try:
        # Выполнение пакетной подписи
        results = batch_signer.sign_documents_batch(
            root_folder=root_folder,
            key_file_path=key_file,
            key_password=key_password,
            extensions=['.pdf'],
            callback_progress=callback_progress
        )
        
        # Статистика
        successful = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success])
        
        message = f"""
        Batch signing completed:
        
        Successful: {successful}
        
        Failed: {failed}
        
        Total time: {time.time() - start_time:.2f}s
        """
        
        
        
    except Exception as e:
        message = f"Batch signing failed: {e}"
        
    finally:
        logging.info(message)
        return message