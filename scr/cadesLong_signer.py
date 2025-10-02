import os, sys, platform
import base64

# Абсолютный путь к каталогу с DLL
DLL_DIR = r"C:\Users\ssamo\Documents\Projects\IITSign\Modules"

os.add_dll_directory(DLL_DIR)
os.environ["PATH"] = DLL_DIR + os.pathsep + os.environ.get("PATH", "")
# (опционально) гарантируем 64-битный Python
assert platform.architecture()[0] == "64bit", "Нужен 64-битный Python"

from Modules.EUSignCP import *

def sign_file_cades_x_long(key_file_path, key_password, file_path):
    if isinstance(key_password, str):
        key_password = key_password.encode("utf-8")
    
    # Чтение JKS файла
    with open(key_file_path, "rb") as f:
        jks_bytes = f.read()
    
    # Чтение файла для подписи
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    EULoad()
    iface = EUGetInterface()
    
    tsp_settings = {
        "bGetStamps": True,
        "szAddress": "http://acskidd.gov.ua/services/tsp/",
        "szPort": "80"
    }
    
    lib_ctx = []
    pk_ctx = []
    
    try:
        iface.Initialize()
        
        dSettings = {}
        dSettings["bUseCMP"] = True
        dSettings["szAddress"] = "http://uakey.com.ua/services/cmp/"
        dSettings["szPort"] = "80"
        dSettings["szCommonName"] = ""
        iface.SetCMPSettings(dSettings)
        
        dSettings = {}
        dSettings["bUseOCSP"] = True
        dSettings["bBeforeStore"] = False
        dSettings["szAddress"] = "http://uakey.com.ua/services/ocsp"
        dSettings["szPort"] = "80"
        iface.SetOCSPSettings(dSettings)
        
        dSettings = {}
        dSettings["bGetStamps"] = True
        dSettings["szAddress"] = "http://acskidd.gov.ua/services/tsp/"
        dSettings["szPort"] = "80"
        iface.SetTSPSettings(tsp_settings)
        iface.CtxCreate(lib_ctx)
        
        # 1) выбрать alias из JKS
        alias_out = []
        idx = 0
        chosen_alias = None
        
        while True:
            try:
                alias_out.clear()
                iface.EnumJKSPrivateKeys(jks_bytes, len(jks_bytes), idx, alias_out)
                if not alias_out:
                    break
                alias = alias_out[0]
                chosen_alias = alias
                break  # берем первый
            except Exception:
                break
            finally:
                idx += 1
        
        if not chosen_alias:
            raise ValueError("В JKS не найден ни один приватный ключ (alias).")
        
        # 2) извлечь приватный ключ из JKS для выбранного alias
        pk_blob_out = []
        certs_count_out = []
        iface.GetJKSPrivateKey(jks_bytes, len(jks_bytes), chosen_alias, pk_blob_out, certs_count_out)
        pk_blob = pk_blob_out[0]
        
        # 3) загрузить приватный ключ в контекст
        owner_info = {}
        iface.CtxReadPrivateKeyBinary(lib_ctx[0], pk_blob, len(pk_blob), key_password, pk_ctx, owner_info)
        
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
            raise RuntimeError("Не удалось получить собственный сертификат из ключа")
        
        cert_bytes = cert_bytes_out[0]
        cert_info2 = {}
        iface.ParseCertificateEx(cert_bytes, len(cert_bytes), cert_info2)
        key_type = cert_info2.get('dwPublicKeyType')
        
        if key_type is None:
            raise RuntimeError(f"Не удалось распарсить сертификат: {cert_info2}")
        
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
            raise ValueError("Неподдерживаемый тип ключа в сертификате")
        
        # 6) хэширование данных файла
        digest_out = []
        iface.CtxHashData(lib_ctx[0], hash_algo, None, 0, file_data, len(file_data), digest_out)
        
        if not digest_out or not digest_out[0]:
            raise RuntimeError("Не удалось получить digest файла")
        
        print("Digest length:", len(digest_out[0]))
        
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
        # empty_sign_str, empty_sign_bytes = [], []
        # iface.CreateEmptySign(file_data, len(file_data), empty_sign_str, empty_sign_bytes)

        output_filename = file_path + ".p7s"
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
        
        with open(output_filename, "rb") as f:
            signed_blob = f.read()

        return signed_blob, output_filename
        
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
        
        try:
            iface.Finalize()
        except Exception:
            pass
        
        EUUnload()
    