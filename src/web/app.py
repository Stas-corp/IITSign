import os
import json
from dotenv import load_dotenv
from pathlib import Path

import streamlit as st

from src.utils.utils import remove_signed_files
from src.sign.signer import main as signer


load_dotenv()

# Настройка страницы
st.set_page_config(
    page_title="Підписи",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

KEYS_FILES = dict(json.loads(os.getenv("ALL_KEYS")))
# KEY = os.getenv("KEY")
KEYS_FOLDER = Path(r'src\sign\keys')
KEYS_FILES = {
    key: {
        "key": Path(key), 
        "sert": Path(sert)} 
    for key, sert in KEYS_FILES.items()
}

class StreamlitApp:
    def __init__(self):
        """Инициализация приложения"""
        self.initialize_session_state()
        # self.module_manager = ModuleManager()
        
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
        
        if "dell_sign" in st.session_state:
            if st.session_state.dell_sign:
                st.toast("Підписи видалено!", icon="✅")
                st.session_state.dell_sign = False
    
    def render_sidebar(self):
        """Отрисовка бокового меню"""
        with st.sidebar:
            st.title("🔑 CAdES-X Long Signer")

            st.markdown("---")
            company_signer = KEYS_FILES.keys()
            signer_radio = st.radio(
                "✍️ Компанія підпису ", 
                company_signer,
                key="company_signer",
            )
            if signer_radio:
                st.session_state.key_path = KEYS_FOLDER / KEYS_FILES[signer_radio]["key"]
                st.session_state.sert_path = KEYS_FOLDER / KEYS_FILES[signer_radio]["sert"]
                
            workers_num = st.slider(
                "Обери кількість потоків:",
                min_value=1,
                max_value=48,
                value=10,
                step=1,
                key='workers_num'
            )
            
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 6, 1])
            with col2:
                st.subheader("⚡ Швидкі дії")
                
                @st.dialog("Видалення всіх пдписів")
                def dell_signs():
                    if st.session_state.root_folder != "":
                        st.write("Шлях для видалення:")
                        st.success(f"{st.session_state.root_folder}")
                        st.warning(f"""
                            ## ⚠️ Увага!
                            
                            Буде видалено всі підписи, які знаходятся в кінцевих папках за шляхом!""")
                        ok = st.button("Підтвердити")
                        if ok:
                            remove_signed_files(st.session_state.root_folder)
                            st.session_state.dell_sign = True
                            st.rerun()
                    else:
                        st.warning("""
                            ## ⚠️ Не ваказано шлях до папки! 
                            
                            Вкажіть шлях в полі на головній сторінці.""")
                
                if st.button("❌ Видалити підписи", "sign_dell_button"):
                    if st.dialog("Видалення всіх пдписів"):
                        dell_signs()
                        
                # if st.button("🗑️ Очистить логи", "log_cleaner_button"):
                #     st.session_state.logs = []
                #     self.add_log("info", "Логі очіщєні")
                #     st.rerun()
    
    def render_home_page(self):
        
        """Главная страница"""
        st.title("⚖️ Підпис файлів для ЕС")
        
        st.markdown("---")
        
        if not st.session_state.sign_btn:
            root_folder = st.text_input(
                "Введіть шлях до локальної папки з документами",
                key="root_folder",
                # disabled=st.session_state.sign_btn
            )
            key_password = st.text_input(
                "Пароль к ключу",
                type="password",
                key="key_password"
                # disabled=st.session_state.sign_btn
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
                sign_btn = st.button(
                    "✅ Підписати пакет документів", 
                    disabled=st.session_state.sign_btn,
                    key="sign_btn"
                )
            else:
                sign_btn = st.button(
                    "🚫 Підписати пакет документів", 
                    disabled=True
                )
        
        if st.session_state.sign_btn:
            start = st.success("✅ Розпочато підпис пакету документів...")
            info = st.warning('УВАГА!\nНЕ ЗАКРИВАТИ ЦЕ ВІКНО І НЕ ПЕРЕХОДИТИ НА ІНШІ МОДУЛІ ПІСЛЯ СТАРТУ', icon="⚠️")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(total, done):
                progress = int(done / total * 100)
                progress_bar.progress(progress)
                status_text.text(f"Підписано {done} з {total} документів")
            
            print(st.session_state.key_path,
            st.session_state.sert_path)
            
            with st.spinner("Підписування...", show_time=True):
                signer(
                    root_folder=st.session_state.root_folder,
                    key_file=st.session_state.key_path,
                    cert_file=st.session_state.sert_path,
                    key_password=st.session_state.key_password,
                    workers=st.session_state.workers_num,
                    callback_progress=update_progress
                )
            start.text("✅ Обробка закінчена!")
            progress_bar.empty()
            info.empty()
            
            st.session_state.sign_btn = False
            if st.button('Підписати знов'):
                st.rerun()
            
        # Последние логи
        # st.markdown("---")
        # st.subheader("📋 Logs")
        
        # if st.session_state.logs:
        #     # Показываем последние 5 записей
        #     recent_logs = st.session_state.logs[-5:]
        #     for log in reversed(recent_logs):
        #         level_color = {
        #             'info': '🔵',
        #             'success': '✅',
        #             'warning': '⚠️',
        #             'error': '❌'
        #         }.get(log['level'], '📝')
                
        #         st.write(f"{level_color} **{log['timestamp']}** - {log['message']}")
        # else:
        #     st.info("Нема подій")
    
    def run(self):
        """Запуск приложения"""
        self.render_sidebar()
        if st.session_state.current_page == 'home':
            self.render_home_page()

# Запуск приложения
if __name__ == "__main__":
    app = StreamlitApp()
    app.run()