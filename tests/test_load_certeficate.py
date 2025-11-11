import pytest
import logging
import platform

from src.sign.signManager import EUSignCPManager

logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s %(levelname)s [%(module)s:%(funcName)s] %(message)s',
        handlers=[
            logging.FileHandler('test.log'),  # В файл
            logging.StreamHandler()            # В консоль
        ]
    )     

def test():
    if platform.system() == "Windows":
        manager = EUSignCPManager(
            r"C:\Users\ssamo\Documents\Projects\IITSign\src\sign\keys\stas.jks",
            r"C:\Users\ssamo\Documents\Projects\IITSign\src\sign\keys\Stas.crt" 
        )
    elif platform.system() == "Linux":
        manager = EUSignCPManager(
            r"/app/src/sign/keys/stas.jks",
            r"/app/src/sign/keys/Stas.crt"
        )
    
    
    print(manager.load_and_check_certificate())