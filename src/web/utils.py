from datetime import datetime

import streamlit as st

def add_log(level: str, message: str):
    """Добавить запись в лог"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append({
        'timestamp': timestamp,
        'level': level,
        'message': message
    })
    # Ограничиваем количество логов
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]