FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libc6 \
    libgcc-s1 \
    libstdc++6 \
    curl \
    gnupg \
    unixodbc-dev \
    unixodbc \
    locales \
    && sed -i -e 's/# uk_UA.UTF-8 UTF-8/uk_UA.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

COPY requieremnts.txt ./requieremnts.txt
RUN pip install --no-cache-dir -r requieremnts.txt

# Создание директорий для данных и ключей
RUN mkdir -p /app/data /app/src/sign/keys /data/certificates

COPY ./data_certs/CACertificates.p7b /data/certificates/CACertificates.p7b
# Копирование файлов проекта
COPY . .

# Настройка переменных окружения
ENV LANG=uk_UA.UTF-8
ENV LC_ALL=uk_UA.UTF-8
ENV LANGUAGE=uk_UA:uk
ENV LD_LIBRARY_PATH=/app/ModulesUNIX:$LD_LIBRARY_PATH
ENV DLL_DIR=/app/ModulesUNIX
ENV PYTHONPATH=/app

# Открытие порта
EXPOSE 63370

# Команда запуска
CMD ["python", "web_app.py"]