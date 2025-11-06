from io import BytesIO
from queue import Queue
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from typing import Optional, Union

class SignTask(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    file_path: Union[str, Path]
    key_file_path: Union[str, Path, BytesIO, bytes]
    key_password: str
    complet_task: Queue
    is_sign_Long_type: Optional[bool] = True
    output_dir: Optional[str] = None
    atempts: int = 0


class SignResult(BaseModel):
    file_path: str
    output_path: bytes
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0
