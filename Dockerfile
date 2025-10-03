FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libc6 \
    libgcc-s1 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY . .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requieremnts.txt

# Создание директорий для данных
RUN mkdir -p /app/data /app/src/sign/keys

# Настройка переменных окружения
ENV LD_LIBRARY_PATH=/app/ModulesUNIX:$LD_LIBRARY_PATH
ENV DLL_DIR=/app/ModulesUNIX
ENV PYTHONPATH=/app
ENV KEY=pb_3696803611.jks
ENV PASS=LALA2108
ENV STREAMLIT_SERVER_PORT=63370
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Открытие порта
EXPOSE 63370

# Команда запуска
CMD ["python", "web_app.py"]