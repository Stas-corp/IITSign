from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Union

class SignTask(BaseModel):
    file_path: Union[str, Path]
    key_file_path: Union[str, Path]
    key_password: str
    output_dir: Optional[str] = None


class SignResult(BaseModel):
    file_path: str
    output_path: bytes
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0
