import os
import sys
import base64
import logging
import platform

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
    # is_sign_Long_type: bool,
    target_file_path: str,
    output_dir: Optional[str] = None,
) -> Tuple[bytes, str]:
    """
    Функция подписи файла.
    
    # Важно!
    
    Для запуска обязательно нужна инициализация библиотеки 
    
    и инстант класса `EUSignCPManager`
    (инициализация библиотеки внутри)
    """
    if isinstance(key_password, str):
        key_password = key_password.encode("utf-8")
    
    # orig_path = Path(target_file_path)
    
    # tmp_dir = tempfile.gettempdir()
    # tmp_ascii_path = Path(tmp_dir) / "temp_to_sign.pdf"
    
    # logging.info("[TEMP SIGN] Copying file to ASCII path: %s", tmp_ascii_path)
    # shutil.copy(orig_path, tmp_ascii_path)
    
    # target_file_path = str(tmp_ascii_path)
    
    # Чтение файла для подписи
    with open(target_file_path, "rb") as f:
        file_data = f.read()
    
    # if is_sign_Long_type:
    #     sign_type = EU_SIGN_TYPE_CADES_X_LONG # Тип подписи CAdES-X Long
    # else: 
    #     sign_type = EU_SIGN_TYPE_CADES_BES
    
    lib_ctx = []
    pk_ctx = []
    
    try:
        iface.CtxCreate(lib_ctx)
        
        owner_info = {}
        iface.CtxReadPrivateKeyBinary(
            lib_ctx[0],           # контекст библиотеки
            key_bytes,            # бинарные данные ZS2 файла
            len(key_bytes),       # длина данных
            key_password,         # пароль ключа
            pk_ctx,              # выходной контекст приватного ключа
            owner_info           # информация о владельце
        )
        
        # получить собственный сертификат
        # cert_info = {}
        # cert_bytes_out = []
        # iface.CtxGetOwnCertificate(
        #     pk_ctx[0],
        #     EU_CERT_KEY_TYPE_UNKNOWN,
        #     EU_KEY_USAGE_DIGITAL_SIGNATURE,
        #     cert_info,
        #     cert_bytes_out
        # )
        
        # if not cert_bytes_out or not cert_bytes_out[0]:
        #     raise RuntimeError("Error get certificate")
        
        # cert_bytes = cert_bytes_out[0]
        # cert_info2 = {}
        # iface.ParseCertificateEx(
        #     cert_bytes, 
        #     len(cert_bytes), 
        #     cert_info2
        # )
        
        # if cert_info2 is None:
        #     raise RuntimeError(f"Error parsing certificate {cert_info2}")
        
        sign_algo = EU_CTX_SIGN_DSTU4145_WITH_GOST34311
        # hash_algo = EU_CTX_HASH_ALGO_GOST34311
        
        # # хэширование данных файла
        # digest_out = []
        # iface.CtxHashData(
        #     lib_ctx[0], 
        #     hash_algo, 
        #     None, 
        #     0, 
        #     file_data, 
        #     len(file_data), 
        #     digest_out
        # )
        
        # if not digest_out or not digest_out[0]:
        #     raise RuntimeError("Error get digest file")
        
        # создание подписи с метками времени
        # signer = []
        # iface.CtxCreateSignerEx(
        #     pk_ctx[0],
        #     sign_algo,
        #     digest_out[0], len(digest_out[0]),
        #     False,  # bNoContentTimeStamp = False для включения меток времени
        #     sign_type,  # Тип подписи
        #     signer
        # )
            # raise RuntimeError()
        
        # # Добавить валидационные данные К SIGNER (не к всей подписи!)
        # up_signer_str, up_signer_bytes = [], []
        # iface.AppendValidationDataToSignerEx(
        #     None,
        #     signer[0], len(signer[0]),
        #     cert_bytes, len(cert_bytes),
        #     sign_type,
        #     up_signer_str, up_signer_bytes
        # )

        # # Получить итоговый signer как bytes
        # if up_signer_bytes and up_signer_bytes[0]:
        #     final_signer = up_signer_bytes[0]
        # elif up_signer_str and up_signer_str[0]:
        #     final_signer = base64.b64decode(up_signer_str[0])
        # # else:
        # #     # если сервисы TSP/OCSP не ответили, можно использовать исходный raw_signer как fallback
        # #     final_signer = signer[0]
        
        # Собрать контейнер: пустая подпись данных -> добавить signer
        # output_filename = target_file_path + ".p7s"
        
        # logging.info("sys.getfilesystemencoding=%s", sys.getfilesystemencoding())
        # logging.info("target_file_path repr: %r", target_file_path)
        # logging.info("target_file_path bytes (utf-8): %r", target_file_path.encode('utf-8', errors='replace'))
        # logging.info("target_file_path bytes (cp1251): %r", None if not isinstance(target_file_path, str) else target_file_path.encode('cp1251', errors='replace'))
        
        # # создаём "пустую" подпись-файл под исходный файл (detached)
        # iface.CtxCreateEmptySignFile(
		# 	lib_ctx[0],
		# 	sign_algo,
		# 	None,
		# 	cert_bytes, len(cert_bytes),
		# 	output_filename
		# )

		# # добавляем тип подписи signer в подпись-файл
        # """
        # pvContext:			object,	// Вхідний. Показчик на контекст 
		# 						// бібліотеки
		# dwSignAlgo:			long,		// Вхідний. Алгоритм підпису, повинен
		# 						// відповідати алгоритму попереднього 
		# 						// підпису
		# pbSigner:			bytes,	// Вхідний. Інформація про 
		# 						// підписувача у вигляді масиву байт
		# dwSignerLength:		long,		// Вхідний. Розмір інформації 
		# 						// про підписувача у вигляді масиву
		# 						// байт
		# pbCertificate:		bytes,	// Вхідний. Сертифікат підписувача.
		# 						// Якщо параметр дорівнює None
		# 						// сертифікат до підпису не додається
		# dwCertificateLength:	long,		// Вхідний. Розмір
		# 						// сертифіката підписувача.
		# pszFileNameWithPreviousSign:	str,	// Вхідний. Ім’я 
		# 						// файлу з попереднім підписом
		# 						// (якщо тип підпису зовнішній)
		# 						// або підписаними даними 
		# 						// (якщо тип підпису внутрішній)
		# pszFileNameWithSign:	str)		// Вхідний. Ім’я файлу, в 
		# 						// який необхідно записати 
		# 						// підпис (якщо тип підпису 
		# 						// зовнішній) або підписані дані 
		# 						// (якщо тип підпису внутрішній)
        # """
        # iface.CtxAppendSignerFile(
		# 	lib_ctx[0], 
		# 	sign_algo,
		# 	final_signer, 
        #     len(final_signer),
		# 	cert_bytes, 
        #     len(cert_bytes),
		# 	output_filename,
		# 	output_filename
		# )
        
        sign_out_bytes = []
        
        iface.CtxSignData(
            pk_ctx[0],           # pvPrivateKeyContext - контекст приватного ключа
            sign_algo,           # dwSignAlgo - алгоритм подписи
            file_data,           # pbData - данные для подписи
            len(file_data),      # dwDataLength - размер данных
            True,                # bExternal = True - внешняя подпись (detached)
            True,                # bAppendCert = True - включить сертификат
            sign_out_bytes       # ppbSign - выходной массив с подписью
        )
        
        # Получаем подпись как bytes
        if not sign_out_bytes or not sign_out_bytes[0]:
            raise RuntimeError("Failed to create signature")
        
        signature_data = sign_out_bytes[0]
        
        if output_dir:
            output_filename = os.path.join(output_dir, os.path.basename(target_file_path) + ".p7s")
        else:
            output_filename = target_file_path + ".p7s"
        
        with open(output_filename, "wb") as f:
            f.write(signature_data)

        return signature_data, output_filename
        
    finally:
        try:
            if pk_ctx:
                iface.CtxFreePrivateKey(pk_ctx[0])
        except Exception:
            pass
        
        try:
            if lib_ctx:
                iface.CtxFree(lib_ctx[0])
        except Exception:
            pass