import os
import threading
import logging

# Абсолютный путь к каталогу с DLL
DLL_DIR = r"C:\Users\ssamo\Documents\Projects\IITSign\Modules"

os.add_dll_directory(DLL_DIR)
os.environ["PATH"] = DLL_DIR + os.pathsep + os.environ.get("PATH", "")

from Modules.EUSignCP import *

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
    
    def __del__(self):
        """Cleanup при завершении"""
        try:
            if hasattr(self, 'iface'):
                self.iface.Finalize()
            EUUnload()
        except:
            pass