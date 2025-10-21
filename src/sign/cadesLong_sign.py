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
    key_bytes: str,
    key_password: str,
    target_file_path: str,
    output_dir: Optional[str] = None,
    
) -> Tuple[bytes, str]:
    """
    Підпис через глобальні налаштування типу підпису
    """
    try:
        with open(target_file_path, "rb") as f:
            file_data = f.read()
        
        owner_info = {}
        iface.ReadPrivateKeyBinary(
            key_bytes, len(key_bytes),
            key_password.encode('utf-8'),
            owner_info
        )
        # Простий підпис - тип береться з глобальних налаштувань
        signed_data_bytes = []
        try:
            iface.SignData(
                file_data, len(file_data),
                None,  # не нужен BASE64
                signed_data_bytes
            )
        except Exception as e:
            logging.error(f"Error create sign data: {e}")
            raise RuntimeError
        
        # logging.info(len(signed_data_bytes))
        
        output_filename = target_file_path + ".p7s"
        if output_dir:
            output_filename = os.path.join(output_dir, 
                os.path.basename(target_file_path) + ".p7s")
        
        with open(output_filename, "wb") as f:
            f.write(signed_data_bytes[0])
        
        return signed_data_bytes[0], output_filename
    
    except Exception as e:
        logging.error(f"Error sign algorithm: {e.args[0]['ErrorCode']} {e.args[0]['ErrorDesc'].decode()}")
        
    finally:
        iface.ResetPrivateKey()