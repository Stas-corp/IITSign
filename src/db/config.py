import os
import dotenv

dotenv.load_dotenv()

USER = os.getenv("DB_USER_ID")
SERVER = os.getenv("DB_SERVER")
DATABASE = os.getenv("DB_NAME")
PASSWORD = os.getenv("DB_PASSWORD")

connection_string = (
    f"mssql+pyodbc://{USER}:{PASSWORD}@{SERVER}:1433/{DATABASE}"
    f"?driver=ODBC+Driver+18+for+SQL+Server"
    f"&TrustServerCertificate=yes"
    f"&Pooling=yes"
)