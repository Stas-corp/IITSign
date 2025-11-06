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
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        key_file_path: str,
        cert_path: str,
        is_sign_Long_type: bool = True
    ):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._initialized = True
                    self.key_file_path = key_file_path
                    self.cert_path = cert_path
                    self.is_sign_Long_type = is_sign_Long_type
                    self._init_library()
    
    
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
            dSettings["szAddress"] = "http://uakey.com.ua/services/ocsp/"
            dSettings["szPort"] = "80"
            self.iface.SetOCSPSettings(dSettings)
            
            dSettings = {}
            dSettings["bGetStamps"] = True
            dSettings["szAddress"] = "http://acskidd.gov.ua/services/tsp/"
            dSettings["szPort"] = "80"
            self.iface.SetTSPSettings(dSettings)
            
            # Включаємо тимчасові мітки TSP (обов'язково для X Long)
            self.iface.SetRuntimeParameter(
                "SignIncludeContentTimeStamp",
                True
            )
            # Включаємо сертифікати ЦСК
            self.iface.SetRuntimeParameter(
                "SignIncludeCACertificates",
                True
            )
            # Встановлюємо тип підпису глобально
            if self.is_sign_Long_type:
                sign_type = EU_SIGN_TYPE_CADES_X_LONG # 16 - CAdES-X Long
            else:
                sign_type = EU_SIGN_TYPE_CADES_BES
                
            self.iface.SetRuntimeParameter(
                "SignType",  # параметр типу підпису
                sign_type  
            )
            
            logging.info("EUSignCP library initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize EUSignCP: {e}")
            raise
        
        
    def load_key(self) -> bytes:
        with open(self.key_file_path, "rb") as f:
            self.key_bytes = f.read()
        
        return self.key_bytes
    
    
    def load_and_check_certificate(self) -> bool:
        try:
            logging.info(self.cert_path)
            with open(self.cert_path, "rb") as f:
                cert_bytes = f.read()

            cert_len = len(cert_bytes)
            self.iface.SaveCertificate(cert_bytes, cert_len)
            self.iface.RefreshFileStore(True)
            
            try:
                self.iface.CheckCertificate(cert_bytes, cert_len)
                # self.iface.CheckCertificateByOCSP(cert_bytes, cert_len)
                logging.info("Certificate successfully download and check!")
                return True
            except Exception as e:
                logging.error(f"Error check certificate: {e.args[0]["ErrorDesc"].decode()}")
                raise RuntimeError("Error check certificate")
        
        except Exception as e:
            logging.error(f"Error load certificate: {e}")
            return False
        
        
    def load_folder_certificate(
        self, 
        cert_path_folder: str,
        extensions = [".cer", ".crt"]
    ):
        
        print('Start load certificate')
        certificates = []
        def scan_dir(path: Path):
            # Перебор всех элементов в текущей папке
            for item in path.iterdir():
                if item.is_dir():
                    # Рекурсивно обходим подпапку
                    print(item)
                    scan_dir(item)
                elif item.is_file() and item.suffix.lower() in extensions:
                    certificates.append(str(item))
        
        path = Path(cert_path_folder)
        scan_dir(path)
        for cer in certificates:
            self.load_and_check_certificate(cer)
        
        
    def __del__(self):
        """Cleanup при завершении"""
        try:
            if hasattr(self, 'iface'):
                self.iface.Finalize()
            EUUnload()
            logging.info("EUUnload!")
        except:
            pass