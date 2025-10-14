# Используйте совместимый базовый образ Windows с нужной версией Python
FROM mcr.microsoft.com/windows/python:3.12

# Создание рабочей директории
WORKDIR C:\\app

# Копирование requirements-файла
COPY requieremnts.txt requieremnts.txt

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requieremnts.txt

# Создание директорий для данных и ключей (используйте PowerShell)
RUN powershell -Command "New-Item -ItemType Directory -Force -Path C:\\app\\data, C:\\app\\src\\sign\\keys, C:\\app\\eusigncp_store\\Certificates"

# Копирование всех файлов проекта
COPY . .

# Настройка переменных окружения
ENV DLL_DIR="C:\\app\\Modules"
ENV PYTHONPATH="C:\\app"

# Открытие порта (добавьте в docker-compose.yml)
EXPOSE 63370

# Команда запуска
CMD ["python", "web_app.py"]