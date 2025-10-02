from pydantic import BaseModel
from typing import Optional

class SignTask(BaseModel):
    file_path: str
    key_file_path: str
    key_password: str
    output_dir: Optional[str] = None


class SignResult(BaseModel):
    file_path: str
    output_path: bytes
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0
