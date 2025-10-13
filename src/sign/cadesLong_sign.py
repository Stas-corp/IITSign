import os
import base64
import platform
import logging

from typing import Optional, Tuple

if platform.system() == "Windows":
    # Для Windows: .pyd + dll
    from Modules.EUSignCP import *
elif platform.system() == "Linux":
    # Для Linux: .so
    from ModulesUNIX.EUSignCP import *
    
from src.sign.signManager import EUSignCPManager


# def load_certificate(cert_file_path: str) -> bytes:
#     """
#     Загрузка сертификата из файла .crt
#     Поддерживает форматы DER и PEM
#     """
#     with open(cert_file_path, 'rb') as f:
#         cert_data = f.read()
    
#     # Если PEM формат - декодируем Base64
#     if cert_data.startswith(b'-----BEGIN CERTIFICATE-----'):
#         cert_text = cert_data.decode('utf-8')
#         cert_base64 = ''.join([line for line in cert_text.split('\n') 
#                               if not line.startswith('-----')])
#         cert_data = base64.b64decode(cert_base64)
    
#     return cert_data


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
        
        # alias_out = []
        # idx = 0
        # chosen_alias = None
        
        # while True:
        #     try:
        #         alias_out.clear()
        #         iface.EnumJKSPrivateKeys(jks_bytes, len(jks_bytes), idx, alias_out)
        #         if not alias_out:
        #             break
        #         alias = alias_out[0]
        #         chosen_alias = alias
        #         break  # берем первый
        #     except Exception:
        #         break
        #     finally:
        #         idx += 1
        
        # if not chosen_alias:
        #     logging.error("In JKS not find privet key (alias).")
        
        # # 2) извлечь приватный ключ из JKS для выбранного alias
        # pk_blob_out = []
        # certs_count_out = []
        # iface.GetJKSPrivateKey(jks_bytes, len(jks_bytes), chosen_alias, pk_blob_out, certs_count_out)
        # pk_blob = pk_blob_out[0]
        
        # # 3) загрузить приватный ключ в контекст
        # owner_info = {}
        # iface.CtxReadPrivateKeyBinary(lib_ctx[0], pk_blob, len(pk_blob), key_password, pk_ctx, owner_info)
        
        owner_info = {}
        iface.CtxReadPrivateKeyBinary(
            lib_ctx[0],           # контекст библиотеки
            key_bytes,            # бинарные данные ZS2 файла
            len(key_bytes),       # длина данных
            key_password,         # пароль ключа
            pk_ctx,              # выходной контекст приватного ключа
            owner_info           # информация о владельце
        )
        
        # 4) получить собственный сертификат
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
        
        # Загрузка внешнего сертификата
        # cert_bytes = load_certificate(cert_file_path)
        
        # # Парсинг для определения алгоритмов
        # cert_info = {}
        # iface.SaveCertificate(cert_bytes, len(cert_bytes))
        # iface.RefreshFileStore(True)
        # iface.ParseCertificateEx(cert_bytes, len(cert_bytes), cert_info)
        # key_type = cert_info.get('dwPublicKeyType')
        
        # 5) подобрать алгоритмы по типу ключа
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
        
        # 6) хэширование данных файла
        digest_out = []
        iface.CtxHashData(lib_ctx[0], hash_algo, None, 0, file_data, len(file_data), digest_out)
        
        if not digest_out or not digest_out[0]:
            raise RuntimeError("Error get digest file")
        
        # 7) создание подписи CAdES-X Long с метками времени
        signer = []
        iface.CtxCreateSignerEx(
            pk_ctx[0],
            sign_algo,
            digest_out[0], len(digest_out[0]),
            False,  # bNoContentTimeStamp = False для включения меток времени
            EU_SIGN_TYPE_CADES_X_LONG,  # Тип подписи CAdES-X Long
            signer
        )

        # 8) Добавить валидационные данные К SIGNER (не к всей подписи!)
        up_signer_str, up_signer_bytes = [], []
        iface.AppendValidationDataToSignerEx(
            None,                  # pszPreviousSigner (если signer в base64-строке; у нас bytes)
            signer[0], len(signer[0]),   # pbPreviousSigner, len
            cert_bytes, len(cert_bytes),
            EU_SIGN_TYPE_CADES_X_LONG,
            up_signer_str, up_signer_bytes
        )

        # Получить итоговый signer как bytes
        if up_signer_bytes and up_signer_bytes[0]:
            final_signer = up_signer_bytes[0]
        elif up_signer_str and up_signer_str[0]:
            final_signer = base64.b64decode(up_signer_str[0])
        else:
            # если сервисы TSP/OCSP не ответили, можно использовать исходный raw_signer как fallback
            final_signer = signer[0]

        # 9) Собрать контейнер: пустая подпись данных -> добавить signer
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
        iface.CtxAppendSignerFile(
			lib_ctx[0],
			sign_algo,
			final_signer, len(final_signer),
			cert_bytes, len(cert_bytes),
			output_filename,     # previous sign file
			output_filename      # write to same path
		)
        
        if output_dir:
            output_filename = os.path.join(output_dir, os.path.basename(target_file_path) + ".p7s")
        else:
            output_filename = target_file_path + ".p7s"
        
        with open(output_filename, "rb") as f:
            signature_date = f.read()

        return signature_date, output_filename
        
    finally:
        # cleanup code...
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