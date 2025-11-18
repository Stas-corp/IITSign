import pytest
import logging
import platform

from src.sign.signManager import EUSignCPManager

logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s %(levelname)s [%(module)s:%(funcName)s] %(message)s',
        handlers=[
            logging.FileHandler('test.log'),  
            logging.StreamHandler()
        ]
    )     

def test():
    if platform.system() == "Windows":
        manager = EUSignCPManager(
            r"src\sign\keys\stas.jks",
            r"C:\Users\Northern Lights\Documents\Secrets\sign.crt"
        )
    elif platform.system() == "Linux":
        manager = EUSignCPManager(
            r"/app/src/sign/keys/stas.jks",
            # r"/app/src/sign/keys/Stas.crt"
        )
    
    # manager._load_certificate(r"src/sign/keys/CACertificates.p7b")

    print(manager.load_and_check_certificate())