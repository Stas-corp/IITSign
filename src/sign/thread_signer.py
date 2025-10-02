import os
import time
import logging
import threading
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


from src.sign.schema import SignTask, SignResult
from src.sign.signManager import EUSignCPManager
from src.sign.cadesLong_sign import sign_file_cades_x_long

class DocumentSigner:
    """
    Класс для подписи документов с thread-safe операциями
    """
    def __init__(self):
        self.manager = EUSignCPManager()
        self.local_lock = threading.Lock()
        
    def sign_single_file(self, task: SignTask) -> SignResult:
        """
        Подпись одного файла
        """
        start_time = time.time()
        
        try:
        # with self.local_lock:
            result_data, output_file = sign_file_cades_x_long(
                self.manager.iface,
                task.key_file_path, 
                task.key_password, 
                task.file_path
            )
            
            processing_time = time.time() - start_time
            
            return SignResult(
                file_path=task.file_path,
                output_path=output_file,
                success=True,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return SignResult(
                file_path=task.file_path,
                output_path="",
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )

class BatchSigner:
    """
    Класс для пакетной подписи документов
    """
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.signer = DocumentSigner()
        
    def find_documents_to_sign(
        self, 
        root_folder: str, 
        extensions: List[str] = None
    ) -> List[str]:
        """
        Поиск документов для подписи в папках
        """
        if extensions is None:
            extensions = ['.pdf']
        
        documents = []
        root_path = Path(root_folder)
        
        directories = [item for item in root_path.iterdir() if item.is_dir()]
        for dir in directories:
            files = [str(item) for item in dir.iterdir() 
                    if item.is_file() and item.suffix.lower() in extensions]
            print(f"In dir {dir} files with sign {len(files)}")
            documents.extend(files)
        
        return documents
    
    def sign_documents_batch(
        self, 
        root_folder: str, 
        key_file_path: str, 
        key_password: str, 
        extensions: List[str],
        output_base_dir: Optional[str] = None,
    ) -> List[SignResult]:
        """
        Пакетная подпись документов с многопоточностью
        """
        documents = self.find_documents_to_sign(root_folder, extensions)
        if not documents:
            logging.warning(f"No documents found in {root_folder}")
            return []
        
        logging.info(f"Found {len(documents)} documents to sign")
        
        tasks = []
        for doc_path in documents:
            if output_base_dir:
                rel_path = os.path.relpath(doc_path, root_folder)
                output_dir = os.path.join(output_base_dir, os.path.dirname(rel_path))
                os.makedirs(output_dir, exist_ok=True)
            else:
                output_dir = None
            task = SignTask(
                file_path=doc_path,
                key_file_path=key_file_path,
                key_password=key_password,
                output_dir=output_dir
            )
            tasks.append(task)
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.signer.sign_single_file, task): task 
                for task in tasks
            }

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        logging.info(f"✓ Signed: {result.file_path} ({result.processing_time:.2f}s)")
                    else:
                        logging.error(f"✗ Failed: {result.file_path} - {result.error_message}")
                        
                except Exception as e:
                    logging.error(f"✗ Exception for {task.file_path}: {e}")
                    results.append(SignResult(
                        file_path=task.file_path,
                        output_path="",
                        success=False,
                        error_message=str(e)
                    ))
        return results