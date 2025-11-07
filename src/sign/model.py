from dataclasses import dataclass
from typing import Optional, Callable
from pathlib import Path

@dataclass
class SignTask:
    """Задача для подписания файла"""
    file_path: str
    key_password: str
    output_dir: Optional[str] = None
    on_complete: Optional[Callable[[], None]] = None
    
    def get_formatted_path(self) -> str:
        """Возвращает форматированный путь для БД"""
        path = Path(self.file_path)
        return f"{path.parent.name}/{path.name}"


@dataclass
class SignResult:
    """Результат подписания файла"""
    file_path: str
    output_path: str
    success: bool
    processing_time: float = 0.0
    error_message: str = ""


@dataclass
class SignerConfig:
    """Конфигурация для подписания"""
    key_file_path: Path
    cert_file_path: Optional[Path] = None
    is_sign_long_type: bool = True
    max_attempts: int = 10
    retry_delay: int = 10
    max_workers: int = 1
