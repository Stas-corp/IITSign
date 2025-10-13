# Используйте совместимый базовый образ Windows с нужной версией Python
FROM mcr.microsoft.com/windows/nanoserver:ltsc2022

SHELL ["pwsh", "-Command"]
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; \
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Устанавливаем Python 3.12 через Chocolatey
RUN choco install python --version=3.12.0 -y

# Обновляем PATH, чтобы использовать установленный Python
ENV PATH="C:\\Python312;C:\\Python312\\Scripts;${PATH}"

# Создание рабочей директории
WORKDIR C:\\app

# Копирование requirements-файла
COPY requieremnts.txt requieremnts.txt

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requieremnts.txt

# Создание директорий для данных и ключей (используйте PowerShell)
RUN New-Item -ItemType Directory -Path C:\\app\\data, C:\\app\\src\\sign\\keys, C:\\app\\eusigncp_store\\Certificates -Force

# Копирование всех файлов проекта
COPY . .

# Настройка переменных окружения
ENV DLL_DIR="C:\\app\\Modules"
ENV PYTHONPATH="C:\\app"

# Открытие порта (добавьте в docker-compose.yml)
EXPOSE 63370

# Команда запуска
CMD ["python", "web_app.py"]