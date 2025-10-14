import os
import time
import queue
import logging
import threading
from pathlib import Path
from typing import List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.sign.schema import SignTask, SignResult
from src.sign.signManager import EUSignCPManager
from src.sign.cadesLong_sign import sign_file_cades_x_long

class DocsSignCounter:
    def __init__(
        self, 
        total_docs: int
    ):
        self.total_docs = total_docs
        self.signed_docs = 0
    
    
    def increment(self, num=1):
        self.signed_docs += num
        return self.signed_docs
    
    
    def get_value(self):
        return (self.total_docs, self.signed_docs)
    
    
    def check_docks_completed(self):
        return self.signed_docs < self.total_docs


class DocumentSigner:
    """
    Класс для подписи документов с thread-safe операциями
    """
    def __init__(
        self, 
        cert_file_path: Union[str, Path] = None,
    ):
        self.signManager = EUSignCPManager()
        if cert_file_path:
            self.signManager.load_and_check_certificate(cert_file_path)
        
        
    def sign_single_file(self, task: SignTask) -> SignResult:
        """
        Подпись одного файла
        """
        start_time = time.time()
        
        try:
        # with self.local_lock:
            _, output_file = sign_file_cades_x_long(
                iface=self.signManager.iface,
                key_file_path=task.key_file_path,
                key_password=task.key_password, 
                target_file_path=task.file_path
            )
            
            processing_time = time.time() - start_time
            task.complet_task.put(1)
            return SignResult(
                file_path=task.file_path,
                output_path=output_file,
                success=True,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            task.complet_task.put(1)
            logging.error(f"Error sign CAdES-X Long: {e}")
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
    def __init__(
        self, 
        cert_file_path: Union[str, Path] = None,
        max_workers: int = 10
    ):
        self.max_workers = max_workers
        self.signer = DocumentSigner(cert_file_path)
        
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
            unsigned_files = []
            for file in dir.iterdir():
                if file.is_file() and file.suffix.lower() in extensions:
                    signature_file = file.with_suffix(file.suffix + '.p7s')
                    if not signature_file.exists():
                        unsigned_files.append(file)
            
            print(f"In dir {dir} files with sign {len(unsigned_files)}")
            documents.extend(str(f) for f in unsigned_files)
        
        return documents
    
    
    def sign_documents_batch(
        self, 
        root_folder: str, 
        key_file_path: Union[str, Path],
        key_password: str, 
        extensions: List[str],
        output_base_dir: Optional[str] = None,
        callback_progress: Callable = None
    ) -> List[SignResult]:
        """
        Пакетная подпись документов с многопоточностью
        """
        progress_queue = queue.Queue()
        
        documents = self.find_documents_to_sign(root_folder, extensions)
        if not documents:
            logging.warning(f"No documents found in {root_folder}")
            return []
        
        docsCounter = DocsSignCounter(len(documents))
        logging.info(f"Found {docsCounter.total_docs} documents to sign")
        
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
                complet_task=progress_queue,
                output_dir=output_dir
            )
            tasks.append(task)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.signer.sign_single_file, task): task 
                for task in tasks
            }
            logging.info(f"Starting threads")
            while docsCounter.check_docks_completed() or any(f.running() for f in futures):
                try:
                    progress_queue.get(timeout=0.2)
                    docsCounter.increment()
                    if callback_progress:
                        callback_progress(*docsCounter.get_value())
                except queue.Empty:
                    pass

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # if result.success:
                    #     logging.info(f"✓ Signed: {result.file_path} ({result.processing_time:.2f}s)")
                    # else:
                    #     logging.error(f"✗ Failed: {result.file_path} - {result.error_message}")
                        
                except Exception as e:
                    logging.error(f"✗ Exception for {task.file_path}: {e}")
                    results.append(SignResult(
                        file_path=task.file_path,
                        output_path="",
                        success=False,
                        error_message=str(e)
                    ))
        return results