import time
import logging
from pathlib import Path
from typing import Callable, Union

from src.sign.thread_signer import BatchSigner

def main(
    root_folder: str,
    key_file: str,
    is_Long_sign: bool,
    key_password: str, 
    workers: int = 10,
    cert_file: Union[str, Path] = None,
    callback_progress: Callable = None
):   
    batch_signer = BatchSigner(
        sign_Long_type=is_Long_sign,
        key_file_path=key_file,
        cert_file_path=cert_file,
        max_workers=workers,
        atempts=3
    )
    start_time = time.time()
    try:
        # Выполнение пакетной подписи
        results = batch_signer.sign_documents_batch(
            root_folder=root_folder,
            key_password=key_password,
            extensions=['.pdf', '.doc'],
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