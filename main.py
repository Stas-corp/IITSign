import os
import dotenv

from scr.cadesLong_signer import sign_file_cades_x_long

dotenv.load_dotenv()

key = os.getenv("KEY")
password = os.getenv("PASS")

if __name__ == "__main__":
    signature_data, output_file = sign_file_cades_x_long(
        key, 
        password, 
        "EUSignPythonAppendixI.doc"
    )
    print(f"Подпись создана успешно. Размер: {len(signature_data)} байт")
    print(f"Файл сохранен: {output_file}")