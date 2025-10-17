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
    output_dir: Optional[str] = None
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
    
    # Чтение key файла
    with open(key_file_path, "rb") as f:
        key_bytes = f.read()
    
    # Чтение файла для подписи
    with open(target_file_path, "rb") as f:
        file_data = f.read()
    
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
        cert_info = {}
        cert_bytes_out = []
        iface.CtxGetOwnCertificate(
            pk_ctx[0],
            EU_CERT_KEY_TYPE_UNKNOWN,
            EU_KEY_USAGE_DIGITAL_SIGNATURE,
            cert_info,
            cert_bytes_out
        )
        
        if not cert_bytes_out or not cert_bytes_out[0]:
            raise RuntimeError("Error get certificate")
        
        cert_bytes = cert_bytes_out[0]
        cert_info2 = {}
        iface.ParseCertificateEx(cert_bytes, len(cert_bytes), cert_info2)
        key_type = cert_info2.get('dwPublicKeyType')
        
        if key_type is None:
            raise RuntimeError(f"Error parsing certificate {cert_info2}")
        
        # подобрать алгоритмы по типу ключа
        if key_type == EU_CERT_KEY_TYPE_ECDSA:
            sign_algo = EU_CTX_SIGN_ECDSA_WITH_SHA
            hash_algo = EU_CTX_HASH_ALGO_SHA256
        elif key_type == EU_CERT_KEY_TYPE_RSA:
            sign_algo = EU_CTX_SIGN_RSA_WITH_SHA
            hash_algo = EU_CTX_HASH_ALGO_SHA256
        elif key_type == EU_CERT_KEY_TYPE_DSTU4145:
            sign_algo = EU_CTX_SIGN_DSTU4145_WITH_DSTU7564
            hash_algo = EU_CTX_HASH_ALGO_DSTU7564_256
        else:
            raise ValueError("Unsupported type key in certificate")
        
        # хэширование данных файла
        digest_out = []
        iface.CtxHashData(lib_ctx[0], hash_algo, None, 0, file_data, len(file_data), digest_out)
        
        if not digest_out or not digest_out[0]:
            raise RuntimeError("Error get digest file")
        
        # создание подписи CAdES-X Long с метками времени
        signer = []
        iface.CtxCreateSignerEx(
            pk_ctx[0],
            sign_algo,
            digest_out[0], len(digest_out[0]),
            False,  # bNoContentTimeStamp = False для включения меток времени
            EU_SIGN_TYPE_CADES_X_LONG,  # Тип подписи CAdES-X Long
            signer
        )

        # Добавить валидационные данные К SIGNER (не к всей подписи!)
        up_signer_str, up_signer_bytes = [], []
        iface.AppendValidationDataToSignerEx(
            None,
            signer[0], len(signer[0]),
            cert_bytes, len(cert_bytes),
            EU_SIGN_TYPE_CADES_X_LONG,
            up_signer_str, up_signer_bytes
        )

        # Получить итоговый signer как bytes
        if up_signer_bytes and up_signer_bytes[0]:
            final_signer = up_signer_bytes[0]
        elif up_signer_str and up_signer_str[0]:
            final_signer = base64.b64decode(up_signer_str[0])
        # else:
        #     # если сервисы TSP/OCSP не ответили, можно использовать исходный raw_signer как fallback
        #     final_signer = signer[0]
        
        # Собрать контейнер: пустая подпись данных -> добавить signer
        output_filename = target_file_path + ".p7s"
        # создаём "пустую" подпись-файл под исходный файл (detached)
        iface.CtxCreateEmptySignFile(
			lib_ctx[0],
			sign_algo,
			None,
			cert_bytes, len(cert_bytes),
			output_filename
		)

		# добавляем CAdES-X Long signer в подпись-файл
        """
        pvContext:			object,	// Вхідний. Показчик на контекст 
								// бібліотеки
		dwSignAlgo:			long,		// Вхідний. Алгоритм підпису, повинен
								// відповідати алгоритму попереднього 
								// підпису
		pbSigner:			bytes,	// Вхідний. Інформація про 
								// підписувача у вигляді масиву байт
		dwSignerLength:		long,		// Вхідний. Розмір інформації 
								// про підписувача у вигляді масиву
								// байт
		pbCertificate:		bytes,	// Вхідний. Сертифікат підписувача.
								// Якщо параметр дорівнює None
								// сертифікат до підпису не додається
		dwCertificateLength:	long,		// Вхідний. Розмір
								// сертифіката підписувача.
		pszFileNameWithPreviousSign:	str,	// Вхідний. Ім’я 
								// файлу з попереднім підписом
								// (якщо тип підпису зовнішній)
								// або підписаними даними 
								// (якщо тип підпису внутрішній)
		pszFileNameWithSign:	str)		// Вхідний. Ім’я файлу, в 
								// який необхідно записати 
								// підпис (якщо тип підпису 
								// зовнішній) або підписані дані 
								// (якщо тип підпису внутрішній)
        """
        iface.CtxAppendSignerFile(
			lib_ctx[0], 
			sign_algo,
			final_signer, 
            len(final_signer),
			cert_bytes, 
            len(cert_bytes),
			output_filename,
			output_filename
		)
        
        if output_dir:
            output_filename = os.path.join(output_dir, os.path.basename(target_file_path) + ".p7s")
        else:
            output_filename = target_file_path + ".p7s"
        
        with open(output_filename, "rb") as f:
            signature_date = f.read()

        return signature_date, output_filename
        
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