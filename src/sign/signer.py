import time
import logging

from src.sign.thread_signer import BatchSigner

def main(
    root_folder: str,
    key_file: str,
    key_password: str, 
    workers: int = 10
):
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )        
    
    batch_signer = BatchSigner(max_workers=workers)
    start_time = time.time()
    try:
        # Выполнение пакетной подписи
        results = batch_signer.sign_documents_batch(
            root_folder=root_folder,
            key_file_path=key_file,
            key_password=key_password,
            extensions=['.pdf']
        )
        
        # Статистика
        successful = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success])
        
        logging.info(f"Batch signing completed:")
        logging.info(f"  Successful: {successful}")
        logging.info(f"  Failed: {failed}")
        logging.info(f"  Total time: {time.time() - start_time:.2f}s")
        
    except Exception as e:
        logging.error(f"Batch signing failed: {e}")