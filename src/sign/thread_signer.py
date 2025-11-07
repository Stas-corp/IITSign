import os
import time
import queue
import logging
import threading
from pathlib import Path
from typing import Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.sign.model import SignTask, SignResult, SignerConfig
from src.sign.signManager import EUSignCPManager
from src.sign.cadesLong_sign import sign_file_cades_x_long
from src.db.dbManager import DatabaseManager

class ProgressCounter:
    """Простой счётчик для отслеживания прогресса"""
    
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
    
    def increment(self, count: int = 1):
        """Увеличить счётчик"""
        self.completed += count
        return self.completed
    
    def get_value(self) -> tuple[int, int]:
        """Получить (completed, total)"""
        return self.completed, self.total
    
    def is_incomplete(self) -> bool:
        """Проверить, что ещё есть незавершённые задачи"""
        return self.completed < self.total


class FileScanner:
    """Поиск неподписанных файлов"""
    
    def __init__(self, extensions: list[str]):
        self.extensions = [ext.lower() for ext in extensions]
    
    def find_unsigned_files(self, root_folder: Path) -> list[Path]:
        """Найти все неподписанные файлы в директории"""
        unsigned_files = []
        folder_stats: dict[Path, int] = {}
        folder_counter = 0
        
        def scan_directory(path: Path) -> int:
            nonlocal folder_counter
            local_unsigned = 0
            
            try:
                for item in path.iterdir():
                    if item.is_dir():
                        folder_counter += 1
                        logging.info(f"[Folder #{folder_counter}] {item.name}")
                        local_unsigned += scan_directory(item)
                    elif item.is_file() and item.suffix.lower() in self.extensions:
                        signature_file = item.with_suffix(item.suffix + '.p7s')
                        if not signature_file.exists():
                            unsigned_files.append(item)
                            local_unsigned += 1
            except PermissionError:
                logging.warning(f"No access to folder: {path}")
            
            if local_unsigned > 0:
                folder_stats[path] = local_unsigned
            
            return local_unsigned
        
        scan_directory(root_folder)
        
        for path, count in folder_stats.items():
            logging.info(f"Folder {path.name} has {count} unsigned files")
        
        return unsigned_files


class SignatureService:
    """Сервис для подписания файлов с механизмом повторных попыток"""
    
    def __init__(self, config: SignerConfig):
        self.config = config
        self._init_sign_manager()
    
    def _init_sign_manager(self):
        """Инициализация менеджера подписи"""
        self.sign_manager = EUSignCPManager(
            key_file_path=str(self.config.key_file_path),
            cert_path=str(self.config.cert_file_path) if self.config.cert_file_path else None,
            is_sign_Long_type=self.config.is_sign_long_type
        )
        
        if self.config.cert_file_path:
            self.sign_manager.load_and_check_certificate()
        
        self.key_bytes = self.sign_manager.load_key()
    
    def sign_file(self, task: SignTask) -> SignResult:
        """Подписать файл с повторными попытками при ошибках"""
        start_time = time.time()
        last_error = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                output_file = self._perform_signing(task)
                processing_time = time.time() - start_time
                
                if task.on_complete:
                    task.on_complete()
                
                return SignResult(
                    file_path=task.file_path,
                    output_path=output_file,
                    success=True,
                    processing_time=processing_time
                )
            
            except Exception as e:
                last_error = e
                logging.error(
                    f"Error signing CAdES-X Long (attempt {attempt}/{self.config.max_attempts}): {e}"
                )
                
                if attempt < self.config.max_attempts:
                    sleep_time = self.config.retry_delay * attempt
                    time.sleep(sleep_time)
        
        processing_time = time.time() - start_time
        
        if task.on_complete:
            task.on_complete()
        
        return SignResult(
            file_path=task.file_path,
            output_path="",
            success=False,
            error_message=str(last_error),
            processing_time=processing_time
        )
    
    def _perform_signing(self, task: SignTask) -> str:
        """Выполнить операцию подписания"""
        _, output_file = sign_file_cades_x_long(
            iface=self.sign_manager.iface,
            key_bytes=self.key_bytes,
            key_password=task.key_password,
            target_file_path=task.file_path
        )
        return output_file


class BatchOrchestrator:
    """Оркестратор для пакетной подписи документов"""
    
    def __init__(
        self,
        config: SignerConfig,
        extensions: list[str],
        db_manager: Optional[DatabaseManager] = None
    ):
        self.config = config
        self.file_scanner = FileScanner(extensions)
        self.signature_service = SignatureService(config)
        self.db_manager = db_manager
    
    def process_folder(
        self,
        root_folder: Path,
        key_password: str,
        output_base_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> list[SignResult]:
        """Обработать все неподписанные файлы в папке"""
        
        unsigned_files = self.file_scanner.find_unsigned_files(root_folder)
        
        if not unsigned_files:
            logging.warning(f"No unsigned documents found in {root_folder}")
            return []
        
        logging.info(f"Found {len(unsigned_files)} documents to sign")
        
        if self.db_manager:
            file_paths = [str(f) for f in unsigned_files]
            self.db_manager.add_files_for_signing(file_paths, False)
        
        progress_queue = queue.Queue()
        
        tasks = self._create_tasks(
            unsigned_files,
            root_folder,
            key_password,
            output_base_dir,
            progress_queue
        )
        
        return self._execute_batch(tasks, progress_queue, progress_callback)
    
    def _create_tasks(
        self,
        files: list[Path],
        root_folder: Path,
        key_password: str,
        output_base_dir: Optional[Path],
        progress_queue: queue.Queue
    ) -> list[SignTask]:
        """Создать задачи для подписания файлов"""
        
        tasks = []
        
        for file_path in files:
            output_dir = None
            if output_base_dir:
                rel_path = file_path.relative_to(root_folder)
                output_dir = output_base_dir / rel_path.parent
                output_dir.mkdir(parents=True, exist_ok=True)
            
            def on_complete_callback():
                progress_queue.put(1)
            
            task = SignTask(
                file_path=str(file_path),
                key_password=key_password,
                output_dir=str(output_dir) if output_dir else None,
                on_complete=on_complete_callback
            )
            tasks.append(task)
        
        return tasks
    
    def _execute_batch(
        self,
        tasks: list[SignTask],
        progress_queue: queue.Queue,
        callback_progress: Optional[Callable[[int, int], None]]
    ) -> list[SignResult]:
        """Выполнить пакетную обработку задач"""
        results = []
        docs_counter = ProgressCounter(len(tasks))
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self.signature_service.sign_file, task): task
                for task in tasks
            }
            
            logging.info(f"Starting batch processing with {self.config.max_workers} workers")
            
            while docs_counter.is_incomplete() or any(f.running() for f in futures):
                try:
                    # Ждём сигнал о завершении задачи из очереди (timeout 0.2 сек)
                    progress_queue.get(timeout=0.2)
                    
                    # Увеличиваем счётчик
                    docs_counter.increment()
                    
                    # Вызываем callback для обновления UI
                    # ВАЖНО: callback вызывается в ГЛАВНОМ потоке!
                    if callback_progress:
                        callback_progress(*docs_counter.get_value())
                        
                except queue.Empty:
                    # Если очередь пуста, просто продолжаем ожидание
                    pass
            
            for future in as_completed(futures):
                task = futures[future]
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logging.error(f"Exception for {task.file_path}: {e}")
                    results.append(SignResult(
                        file_path=task.file_path,
                        output_path="",
                        success=False,
                        error_message=str(e)
                    ))
        
        logging.info(f"Batch processing completed: {len(results)} files processed")
        return results


class BatchSigner:
    """Фасад для пакетной подписи документов"""
    
    def __init__(
        self,
        key_file_path: Union[str, Path],
        cert_file_path: Optional[Union[str, Path]] = None,
        is_sign_long_type: bool = True,
        max_attempts: int = 10,
        retry_delay: int = 10,
        max_workers: int = 10,
        extensions: Optional[list[str]] = None
    ):
        self.config = SignerConfig(
            key_file_path=Path(key_file_path),
            cert_file_path=Path(cert_file_path) if cert_file_path else None,
            is_sign_long_type=is_sign_long_type,
            max_attempts=max_attempts,
            retry_delay=retry_delay,
            max_workers=max_workers
        )
        
        self.extensions = extensions or ['.pdf']
        self.orchestrator = BatchOrchestrator(
            config=self.config,
            extensions=self.extensions,
            db_manager=None
        )
    
    def sign_documents_batch(
        self,
        root_folder: Union[str, Path],
        key_password: str,
        output_base_dir: Optional[Union[str, Path]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> list[SignResult]:
        """
        Пакетная подпись документов в папке
        
        Args:
            root_folder: Корневая папка для поиска файлов
            key_password: Пароль для ключа
            output_base_dir: Директория для сохранения подписанных файлов
            progress_callback: Callback для отслеживания прогресса (completed, total)
        
        Returns:
            Список результатов подписания
        """
        root_path = Path(root_folder)
        output_path = Path(output_base_dir) if output_base_dir else None
        
        return self.orchestrator.process_folder(
            root_folder=root_path,
            key_password=key_password,
            output_base_dir=output_path,
            progress_callback=progress_callback
        )