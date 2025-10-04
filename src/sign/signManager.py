import os
import sys
import threading
import logging
import platform
from pathlib import Path

# Абсолютный путь к каталогу с DLL
ROOT_DIR = Path(__file__).resolve().parents[2]
MODULES_DIR = ROOT_DIR / "Modules"

sys.path.insert(0, str(ROOT_DIR))

if platform.system() == "Windows":
    # Для Windows: .pyd + dll
    MODULES_DIR = ROOT_DIR / "Modules"
    os.add_dll_directory(str(MODULES_DIR))
    os.environ["PATH"] = str(MODULES_DIR) + os.pathsep + os.environ.get("PATH", "")
    from Modules.EUSignCP import *
elif platform.system() == "Linux":
    # Для Linux: .so
    MODULES_DIR = ROOT_DIR / "ModulesUNIX"
    os.environ["LD_LIBRARY_PATH"] = str(MODULES_DIR) + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
    from ModulesUNIX.EUSignCP import *



class EUSignCPManager:
    """
    Менеджер для работы с EUSignCP.
    Инициализируется один раз и переиспользуется.
    """
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._init_library()
                    self._initialized = True
    
    def _init_library(self):
        """Глобальная инициализация библиотеки"""
        try:
            EULoad()
            self.iface = EUGetInterface()
            self.iface.Initialize()
            
            dSettings = {}
            dSettings["bUseCMP"] = True
            dSettings["szAddress"] = "http://uakey.com.ua/services/cmp/"
            dSettings["szPort"] = "80"
            dSettings["szCommonName"] = ""
            self.iface.SetCMPSettings(dSettings)
            
            dSettings = {}
            dSettings["bUseOCSP"] = True
            dSettings["bBeforeStore"] = False
            dSettings["szAddress"] = "http://uakey.com.ua/services/ocsp"
            dSettings["szPort"] = "80"
            self.iface.SetOCSPSettings(dSettings)
            
            dSettings = {}
            dSettings["bGetStamps"] = True
            dSettings["szAddress"] = "http://acskidd.gov.ua/services/tsp/"
            dSettings["szPort"] = "80"
            self.iface.SetTSPSettings(dSettings)
            
            logging.info("EUSignCP library initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize EUSignCP: {e}")
            raise
        
    def load_and_check_certificate(self, cert_path):
        try:
            # 1. Прочитать файл сертификата
            with open(cert_path, "rb") as f:
                cert_bytes = f.read()
            cert_len = len(cert_bytes)

            # 2. Сохранить сертификат в хранилище
            self.iface.SaveCertificate(cert_bytes, cert_len)

            # 3. Обновить хранилище (перезагрузить список сертификатов)
            self.iface.RefreshFileStore(True)

            # 4. Проверить загруженный сертификат
            #    Если сертификат не найден или некорректен, выбросится исключение
            self.iface.CheckCertificate(cert_bytes, cert_len)
            self.iface.CheckCertificateByOCSP(cert_bytes, cert_len)
		

            logging.info("Certificate successfully download and check!")
            return True

        except Exception as e:
            logging.error("Error checking certificate:", e)
            return False
        
    def __del__(self):
        """Cleanup при завершении"""
        try:
            if hasattr(self, 'iface'):
                self.iface.Finalize()
            EUUnload()
        except:
            pass