import logging
from pathlib import Path
from typing import Optional

from src.sign.signManager import EUSignCPManager
from src.sign.thread_signer import FileScanner

def remove_signed_files(
    root_path_dir: str,
    extensions: Optional[list] = None
):
    if extensions is None:
        extensions = ['.pdf', '.xml']
    file_manager = FileScanner(extensions)
    file_manager.find_unsigned_files(
        root_folder=root_path_dir,
        delete_signatures=True
    )


def analyze_jks_detailed(iface, jks_bytes, key_password):
    """
    Детальный анализ JKS контейнера
    """
    print("=== ДЕТАЛЬНЫЙ АНАЛИЗ JKS ===")
    
    # Перечисление ключей
    idx = 0
    while True:
        try:
            alias_out = []
            iface.EnumJKSPrivateKeys(jks_bytes, len(jks_bytes), idx, alias_out)
            if not alias_out:
                break
            
            alias = alias_out[0]
            print(f"\n--- Alias #{idx}: {alias} ---")
            
            # Извлечение ключа и подсчет сертификатов
            pk_blob_out = []
            certs_count_out = []
            iface.GetJKSPrivateKey(jks_bytes, len(jks_bytes), alias, pk_blob_out, certs_count_out)
            
            print(f"Размер приватного ключа: {len(pk_blob_out[0])} байт")
            print(f"Количество сертификатов: {certs_count_out[0]}")
            
            if certs_count_out[0] == 0:
                print("⚠ ПРОБЛЕМА: Сертификат отсутствует в JKS!")
                return False
            
            # Попытка загрузки ключа
            lib_ctx = []
            pk_ctx = []
            
            try:
                iface.CtxCreate(lib_ctx)
                owner_info = {}
                
                if isinstance(key_password, str):
                    key_password = key_password.encode('utf-8')
                
                iface.CtxReadPrivateKeyBinary(
                    lib_ctx[0], pk_blob_out[0], len(pk_blob_out[0]), 
                    key_password, pk_ctx, owner_info
                )
                
                print("✓ Ключ успешно загружен")
                print(f"Owner info содержит: {list(owner_info.keys())}")
                
                # Проверка сертификата в owner_info
                if 'pbCertificate' in owner_info and owner_info['pbCertificate']:
                    cert_data = owner_info['pbCertificate']
                    print(f"✓ Найден сертификат в owner_info: {len(cert_data)} байт")
                    
                    # Парсинг сертификата
                    try:
                        cert_info = {}
                        iface.ParseCertificateEx(cert_data, len(cert_data), cert_info)
                        print(f"✓ Сертификат успешно распарсен")
                        print(f"  Субъект: {cert_info.get('pszSubjCN', 'N/A')}")
                        print(f"  Издатель: {cert_info.get('pszIssuerCN', 'N/A')}")
                        print(f"  Тип ключа: {cert_info.get('dwPublicKeyType', 'N/A')}")
                        return True
                    except Exception as e:
                        print(f"✗ Ошибка парсинга сертификата: {e}")
                        return False
                else:
                    print("✗ Сертификат не найден в owner_info")
                    return False
                    
            except Exception as e:
                print(f"✗ Ошибка загрузки ключа: {e}")
                return False
            
            finally:
                if pk_ctx:
                    iface.CtxFreePrivateKey(pk_ctx[0])
                if lib_ctx:
                    iface.CtxFree(lib_ctx[0])
            
        except Exception as e:
            print(f"✗ Ошибка обработки alias #{idx}: {e}")
            return False
        finally:
            idx += 1
    
    return False


def load_and_check_certificate(ifase, cert_path):
    
    try:

        # 4. Прочитать файл сертификата
        with open(cert_path, "rb") as f:
            cert_bytes = f.read()
        cert_len = len(cert_bytes)

        # 5. Сохранить сертификат в хранилище
        ifase.SaveCertificate(cert_bytes, cert_len)

        # 6. Обновить хранилище (перезагрузить список сертификатов)
        ifase.RefreshFileStore(True)

        # 7. Проверить загруженный сертификат
        #    Если сертификат не найден или некорректен, выбросится исключение
        ifase.CheckCertificate(cert_bytes, cert_len)
        print("Сертификат успешно загружен и проверен")
        return True

    except Exception as e:
        # Обратите внимание: для детальной обработки можно сравнить код ошибки
        # например, e.args[0] == EUERRORCERTNOTFOUND
        print("Ошибка проверки сертификата:", e)
        return False


def test_jks_container():
    SignMng = EUSignCPManager()
    
    with open(r"src\sign\keys\stas.jks", "rb") as f:
        jks_bytes = f.read()
    
    load_and_check_certificate(SignMng.iface, r"src\sign\keys\Stas.crt")


# if __name__ == "__main__":
#     remove_signed_files(r"C:\Users\ssamo\Documents\Projects\Ace_11_09_2025_part1")