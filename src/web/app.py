import os
import io
import json
import base64
import logging
import zipfile
import tempfile
from pathlib import Path
from typing import Callable

import streamlit as st
from dotenv import load_dotenv
import streamlit.components.v1 as components

from src.utils.utils import remove_signed_files
from src.sign.services import sign_folder_documents
from src.sign.signManager import EUSignCPManager

load_dotenv()

# Настройка страницы
st.set_page_config(
    page_title="Підписи",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

KEYS_FILES = dict(json.loads(os.getenv("ALL_KEYS")))
KEYS_FOLDER = Path('src') / 'sign' / 'keys'
KEYS_FILES = {
    key: {
        "key": Path(key),
        "cert": Path(cert)}
    for key, cert in KEYS_FILES.items()
}


class StreamlitApp:
    def __init__(self):
        """Инициализация приложения"""
        self.initialize_session_state()

    def initialize_session_state(self):
        """Инициализация состояния сессии"""
        if "sign_btn" not in st.session_state:
            st.session_state.sign_btn = False
        if "success_sign" not in st.session_state:
            st.session_state.success_sign = False
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'
        if 'modules_data' not in st.session_state:
            st.session_state.modules_data = {}
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        if 'user_secrets' not in st.session_state:
            st.session_state.user_secrets = False
        if 'key_file' not in st.session_state:
            st.session_state.key_file = False
        if 'cert_file' not in st.session_state:
            st.session_state.cert_file = False
        if "add_user_secrets" not in st.session_state:
            st.session_state.add_user_secrets = False
        if "sign_mode" not in st.session_state:
            st.session_state.sign_mode = 'batch'  # 'batch' або 'single'
        if "uploaded_file" not in st.session_state:
            st.session_state.uploaded_file = None
        if "is_password" not in st.session_state:
            st.session_state.is_password = False
            
        if "add_user_secrets_toast" in st.session_state:
            if st.session_state.add_user_secrets_toast:
                st.toast("Ключ і сертифікат додано!", icon="✅")
                st.session_state.add_user_secrets_toast = False
        if "dell_sign_toast" in st.session_state:
            if st.session_state.dell_sign_toast:
                st.toast("Підписи видалено!", icon="✅")
                st.session_state.dell_sign_toast = False

    def render_sidebar(self):
        """Отрисовка бокового меню"""
        with st.sidebar:
            st.title("🔑 CAdES-X Long Signer")
            st.markdown("---")
            
            # Режим підпису
            sign_mode = st.radio(
                "📝 Режим підпису",
                ['Пакетний підпис', 'Підпис одного файлу'],
                key="sign_mode_radio",
            )
            
            if sign_mode == 'Пакетний підпис':
                st.session_state.sign_mode = 'batch'
            else:
                st.session_state.sign_mode = 'single'
            
            st.markdown("---")
            
            company_signer = []
            # company_signer = list(KEYS_FILES.keys())
            company_signer.append('Окремий підпис')
            
            signer_radio = st.radio(
                "✍️ Компанія підпису",
                company_signer,
                key="company_signer",
            )
            
            if signer_radio != 'Окремий підпис':
                st.session_state.user_secrets = False
                st.session_state.add_user_secrets = False
                st.session_state.key_file = KEYS_FOLDER / KEYS_FILES[signer_radio]["key"]
                st.session_state.cert_file = KEYS_FOLDER / KEYS_FILES[signer_radio]["cert"]
            else:
                st.session_state.user_secrets = True
                if not st.session_state.add_user_secrets:
                    st.session_state.key_file = False
                    st.session_state.cert_file = False
            
            st.checkbox(
                "Використовувати CAdES-X Long підпис",
                value=True,
                key="is_long_sign"
            )
            
            # Показуємо slider тільки для пакетного режиму
            if st.session_state.sign_mode == 'batch':
                st.slider(
                    "Обери кількість потоків:",
                    min_value=1,
                    max_value=17,
                    value=10,
                    step=1,
                    key='workers_num'
                )
            else:
                # Для одного файлу встановлюємо 1 потік
                if 'workers_num' not in st.session_state:
                    st.session_state.workers_num = 1
            
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 6, 1])
            with col2:
                st.subheader("⚡ Швидкі дії")
                if st.button("❌ Видалити підписи"):
                    if st.dialog("Видалення всіх підписів"):
                        self.dell_signs()
    
    
    @st.dialog("Введіть пароль")
    def password_dialog(
        self,
        fuction: Callable[[str], None]
    ):
        password = st.text_input("Пароль:", type="password")
        if st.button("Підтвердити"):
            if password:
                # st.session_state.password = password
                fuction(password)
                st.session_state.is_password = True
                st.rerun()
            else:
                st.error("Введите пароль")
    
    
    @st.dialog("Видалення всіх підписів")
    def dell_signs(self):
        if ("root_folder" in st.session_state and
            st.session_state.root_folder != ""
        ):
            st.write("Шлях для видалення:")
            st.success(f"{st.session_state.root_folder}")
            st.warning(f"""
                ## ⚠️ Увага!
                Буде видалено всі підписи, які знаходятся в кінцевих папках за шляхом!"""
            )
            ok = st.button("Підтвердити")
            if ok:
                remove_signed_files(st.session_state.root_folder)
                st.session_state.dell_sign_toast = True
                st.rerun()
        else:
            st.warning("""
                ## ⚠️ Не вказано шлях до папки!
                Вкажіть шлях в полі на головній сторінці."""
            )

    @st.dialog("Завантажте файли для підпису")
    def download_secrets(self):
        cert_file = st.file_uploader(
            "Файл сертифіката",
            type=["crt", "cer"],
        )
        
        key_file = st.file_uploader(
            "Файл ключа",
            type=["ZS2", "JKS"],
        )
        
        def save_uploaded_to_disk(uploaded_file) -> Path:
            """
            Сохраняет st.file_uploader UploadedFile во временный файл и возвращает pathlib.Path.
            """
            suffix = Path(uploaded_file.name).suffix
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(uploaded_file.getvalue())
            tmp.flush()
            tmp.close()
            return Path(tmp.name)
        
        if key_file:
            st.success("✅ Обидва файли успішно завантажено!")
            if st.button("➡️ Продовжити"):
                st.session_state.cert_file = save_uploaded_to_disk(cert_file) if cert_file else None
                st.session_state.key_file = save_uploaded_to_disk(key_file)
                st.session_state.add_user_secrets = True
                st.session_state.add_user_secrets_toast = True
                logging.info(st.session_state)
                st.rerun()
        else:
            st.warning("⚠️ Завантажте мінімум файл ключа!")

    def render_batch_sign_page(self):
        """Страница пакетного подпису"""
        st.title("⚖️ Пакетний підпис файлів для ЕС")
        st.markdown("---")
        
        if not st.session_state.is_password:
            if st.session_state.user_secrets:
                if st.session_state.key_file:
                    st.success("✅ Ключ і сертифікат завантажено!")
                    cpmng = EUSignCPManager(
                        key_file_path=st.session_state.key_file,
                        cert_path=st.session_state.cert_file
                    )
                    if not st.session_state.cert_file:
                        self.password_dialog(cpmng.load_and_check_certificate)
                    else:
                        cpmng.load_and_check_certificate()
                else:
                    st.warning("⚠️ Необхідно завантажити ключ і сертифікат")
                    load_secret = st.button("🔑 Завантажити ключ і сертифікат")
                    if load_secret:
                        self.download_secrets()
        
        if st.session_state.key_file:
            if not st.session_state.sign_btn:
                root_folder = st.text_input(
                    "Введіть шлях до локальної папки з документами",
                    key="root_folder",
                )
                
                key_password = st.text_input(
                    "Пароль к ключу",
                    type="password",
                    key="key_password"
                )
                
                if not root_folder:
                    st.error("❌ Вкажіть шлях до папки!")
                    st.session_state.push_sign_btn = False
                if not key_password:
                    st.error("❌ Введіть пароль!")
                    st.session_state.push_sign_btn = False
                if root_folder and key_password:
                    st.session_state.push_sign_btn = True
                
                if st.session_state.push_sign_btn:
                    st.button(
                        "✅ Підписати пакет документів",
                        disabled=st.session_state.sign_btn,
                        key="sign_btn"
                    )
                else:
                    st.button(
                        "🚫 Підписати пакет документів",
                        disabled=True
                    )
            
            if st.session_state.sign_btn:
                start = st.success("✅ Розпочато підпис пакету документів...")
                info = st.warning('УВАГА!\nНЕ ЗАКРИВАТИ ЦЕ ВІКНО І НЕ ПЕРЕХОДИТИ НА ІНШІ МОДУЛІ ПІСЛЯ СТАРТУ', icon="⚠️")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(
                    completed: int,
                    total: int,
                    elements_message: str = "документів"
                ):
                    progress = int(completed / total * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Опрацьовано {completed} з {total} {elements_message}")
                
                with st.spinner("Підписування...", show_time=True):
                    success, message = sign_folder_documents(
                        root_folder=st.session_state.root_folder,
                        key_file=st.session_state.key_file,
                        is_long_sign=st.session_state.is_long_sign,
                        cert_file=st.session_state.cert_file,
                        key_password=st.session_state.key_password,
                        workers=st.session_state.workers_num,
                        callback_progress=update_progress
                    )
                
                start.text("✅ Обробка закінчена!")
                if success:
                    st.success(message)
                else:
                    st.error(message)
                
                progress_bar.empty()
                info.empty()
                st.session_state.sign_btn = False
                
                if st.button('Підписати знов'):
                    st.rerun()

    def render_single_sign_page(self):
        """Страница подписи одного файла"""
        
        st.title("📄 Підпис одного файлу")
        st.markdown("---")
        
        if not st.session_state.is_password:
            if st.session_state.user_secrets:
                if st.session_state.key_file:
                    st.success("✅ Ключ і сертифікат завантажено!")
                    cpmng = EUSignCPManager(
                        key_file_path=st.session_state.key_file,
                        cert_path=st.session_state.cert_file
                    )
                    if not st.session_state.cert_file:
                        self.password_dialog(cpmng.load_and_check_certificate)
                    else:
                        cpmng.load_and_check_certificate()
                else:
                    st.warning("⚠️ Необхідно завантажити ключ і сертифікат")
                    load_secret = st.button("🔑 Завантажити ключ і сертифікат")
                    if load_secret:
                        self.download_secrets()
        
        
        if st.session_state.key_file:
            st.subheader("📎 Завантажте файл для підпису")
            
            uploaded_files = st.file_uploader(
                "Виберіть файл",
                type=None,  # Приймаємо будь-які типи файлів
                key="single_file_uploader",
                accept_multiple_files=True
            )
            
            if uploaded_files:
                st.success(f"✅ Файл завантажено!")
                # st.session_state.uploaded_file = uploaded_files
                
                # Шаг 3: Ввод пароля
                st.markdown("---")
                st.subheader("🔐 Введіть пароль")
                
                key_password = st.text_input(
                    "Пароль до ключу",
                    type="password",
                    key="single_key_password"
                )
                
                if key_password:
                    # Кнопка подписи
                    if st.button("✍️ Підписати файл", key="single_sign_btn"):
                        self.sign_single_file(uploaded_files, key_password)
                else:
                    st.error("❌ Введіть пароль!")

    def sign_single_file(
        self,
        uploaded_files,
        key_password
    ):
        """Підпис одного файлу"""
        try:
            # Створюємо тимчасову папку для обробки
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                logging.info(f"temp_file : {temp_path}")
                
                for file in uploaded_files:
                    file_path = temp_path / file.name
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                
                with st.spinner("Підписування...", show_time=True):
                    success, message = sign_folder_documents(
                        root_folder=str(temp_path),
                        key_file=st.session_state.key_file,
                        is_long_sign=st.session_state.is_long_sign,
                        cert_file=st.session_state.cert_file,
                        key_password=key_password,
                        workers=st.session_state.workers_num,
                    )
                
                if success:
                    st.success("✅ Файл успішно підписано!")
                    
                    all_files = list(temp_path.glob("*"))
                    
                    if all_files:
                        # Створюємо архів у пам'яті
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for file in all_files:
                                if file.is_file():
                                    # Додаємо файл до архіву
                                    zip_file.write(file, arcname=file.name)
                        
                        zip_buffer.seek(0)
                        zip_data = zip_buffer.getvalue()
                        
                        # Автоматичне скачування через JavaScript
                        b64_data = base64.b64encode(zip_data).decode()
                        archive_name = f"signed.zip"
                        
                        # HTML + JavaScript для автоматичного завантаження
                        download_html = f"""
                            <html>
                            <head>
                            <script>
                            function downloadFile() {{
                                const b64Data = '{b64_data}';
                                const filename = '{archive_name}';
                                
                                // Конвертуємо base64 в Blob
                                const byteCharacters = atob(b64Data);
                                const byteNumbers = new Array(byteCharacters.length);
                                for (let i = 0; i < byteCharacters.length; i++) {{
                                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                                }}
                                const byteArray = new Uint8Array(byteNumbers);
                                const blob = new Blob([byteArray], {{type: 'application/octet-stream'}});
                                
                                // Створюємо URL для Blob
                                const url = window.URL.createObjectURL(blob);
                                
                                // Створюємо тег <a> і клікаємо на нього
                                const a = document.createElement('a');
                                a.style.display = 'none';
                                a.href = url;
                                a.download = filename;
                                document.body.appendChild(a);
                                a.click();
                                
                                // Очищаємо
                                window.URL.revokeObjectURL(url);
                                document.body.removeChild(a);
                            }}
                            
                            // Запускаємо завантаження при завантаженні сторінки
                            window.onload = downloadFile;
                            </script>
                            </head>
                            <body>
                            </body>
                            </html>
                        """
                        
                        # Відображаємо HTML (автоматично запустить завантаження)
                        components.html(download_html, height=0, width=0)
                        
                        # Кнопка завантаження
                        st.download_button(
                            label="⬇️ Завантажити підписаний файл",
                            data=zip_data,
                            file_name=archive_name,
                            mime="application/zip"
                        )
                        
                        with st.expander("📋 Список файлів у архіві"):
                            for file in all_files:
                                if file.is_file():
                                    st.text(f"📄 {file.name}")
                    else:
                        st.warning("⚠️ Підписаний файл не знайдено")
                else:
                    st.error(f"❌ Помилка підпису: {message}")
                    
        except Exception as e:
            st.error(f"❌ Помилка: {str(e)}")

    def render_home_page(self):
        """Главная страница с выбором режима"""
        if st.session_state.sign_mode == 'batch':
            self.render_batch_sign_page()
        else:
            self.render_single_sign_page()

    def run(self):
        """Запуск приложения"""
        self.render_sidebar()
        if st.session_state.current_page == 'home':
            self.render_home_page()


if __name__ == "__main__":
    app = StreamlitApp()
    app.run()