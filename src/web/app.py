
from pathlib import Path
from datetime import datetime

import streamlit as st

from src.sign.signer import main as signer

# Настройка страницы
st.set_page_config(
    page_title="ASVP",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

KEYS_FOLDER = Path('src\sign\keys')
KEYS_FILES = {
    "Ace": Path('pb_3696803611.jks'),
    "Unit": Path('unit.jks')
}

class StreamlitApp:
    def __init__(self):
        """Инициализация приложения"""
        self.initialize_session_state()
        print(st.session_state)
        # self.module_manager = ModuleManager()
        
    def initialize_session_state(self):
        """Инициализация состояния сессии"""
        
        if "sign_btn" not in st.session_state:
            st.session_state.sign_btn = False
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'
        if 'modules_data' not in st.session_state:
            st.session_state.modules_data = {}
        if 'logs' not in st.session_state:
            st.session_state.logs = []
    
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
                st.session_state.key_path = KEYS_FOLDER / KEYS_FILES.get(signer_radio)
                
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
                
                if st.button("❌ Видалити підписи", "sign_dell_button"):
                    pass
                
                if st.button("🗑️ Очистить логи", "log_cleaner_button"):
                    st.session_state.logs = []
                    self.add_log("info", "Логі очіщєні")
                    st.rerun()
    
    def render_home_page(self):
        if not st.session_state.sign_btn:
            """Главная страница"""
            st.title("⚖️ Пдіпис файлів для ЕС")
            
            st.markdown("---")
            root_folder = st.text_input(
                "Введить шлях до локальної папки з документами",
                key="root_folder")
            
            key_password = st.text_input(
                "Пароль к ключу", 
                type="password")
            
            
            if not root_folder:
                st.error("❌ Вкажіть путь до папки!")
                st.session_state.push_sign_btn = False
            if not key_password:
                st.error("❌ Введіть пароль!")
                st.session_state.push_sign_btn = False
            
            if root_folder and key_password:
                st.session_state.push_sign_btn = True
            
            if st.session_state.push_sign_btn:
                sign_btn = st.button("✅ Підписати пакет документів")
            else:
                sign_btn = st.button("🚫 Підписати пакет документів", disabled=True)
                
            if sign_btn:
                st.session_state.sign_btn = True
                
                signer(
                    root_folder=root_folder,
                    key_file=st.session_state.key_path,
                    key_password=key_password,
                    workers=st.session_state.workers_num
                )
        
        # Последние логи
        st.markdown("---")
        st.subheader("📋 Logs")
        
        if st.session_state.logs:
            # Показываем последние 5 записей
            recent_logs = st.session_state.logs[-5:]
            for log in reversed(recent_logs):
                level_color = {
                    'info': '🔵',
                    'success': '✅',
                    'warning': '⚠️',
                    'error': '❌'
                }.get(log['level'], '📝')
                
                st.write(f"{level_color} **{log['timestamp']}** - {log['message']}")
        else:
            st.info("Нема подій")
    
    def run(self):
        """Запуск приложения"""
        self.render_sidebar()
        if st.session_state.current_page == 'home':
            self.render_home_page()

# Запуск приложения
if __name__ == "__main__":
    app = StreamlitApp()
    app.run()