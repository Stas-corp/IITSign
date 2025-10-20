import os
import base64
import platform
import logging

from typing import Optional, Tuple

if platform.system() == "Windows":
    from Modules.EUSignCP import *
elif platform.system() == "Linux":
    from ModulesUNIX.EUSignCP import *
    
from src.sign.signManager import EUSignCPManager

def sign_file_cades_x_long(
    iface: EUSignCPManager,
    key_file_path: str,
    key_password: str,
    target_file_path: str,
    is_sign_Long_type: bool,
    output_dir: Optional[str] = None,
    
) -> Tuple[bytes, str]:
    """
    Підпис через глобальні налаштування типу підпису
    """
    try:
        iface.Initialize()
        
        # Встановлюємо тип підпису глобально
        if is_sign_Long_type:
            sign_type = EU_SIGN_TYPE_CADES_X_LONG
        else:
            sign_type = EU_SIGN_TYPE_CADES_BES
            
        iface.SetRuntimeParameter(
            "SignType",  # параметр типу підпису
            sign_type  # 16 - CAdES-X Long
        )
        
        # Включаємо тимчасові мітки TSP (обов'язково для X Long)
        iface.SetRuntimeParameter(
            "SignIncludeContentTimeStamp",
            True
        )
        
        # Включаємо сертифікати ЦСК
        iface.SetRuntimeParameter(
            "SignIncludeCACertificates",
            True
        )
        
        # Читаємо ключ
        with open(key_file_path, "rb") as f:
            key_bytes = f.read()
        
        owner_info = {}
        iface.ReadPrivateKeyBinary(
            key_bytes, len(key_bytes),
            key_password.encode('utf-8'),
            owner_info
        )
        
        # Читаємо файл
        with open(target_file_path, "rb") as f:
            file_data = f.read()
        
        # Простий підпис - тип береться з глобальних налаштувань
        signed_data_bytes = []
        
        iface.SignData(
            file_data, len(file_data),
            None,  # не потрібен BASE64
            signed_data_bytes
        )
        
        logging.info(len(signed_data_bytes))
        
        output_filename = target_file_path + ".p7s"
        if output_dir:
            output_filename = os.path.join(output_dir, 
                os.path.basename(target_file_path) + ".p7s")
        
        with open(output_filename, "wb") as f:
            f.write(signed_data_bytes[0])
        
        return signed_data_bytes[0], output_filename
        
    finally:
        iface.ResetPrivateKey()