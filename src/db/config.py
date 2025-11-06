import os
import dotenv

dotenv.load_dotenv()

def connection_string(
    db_name: str = None,
    is_local: bool = False,
    is_conteiner: bool = False
) -> str:
    prefix = ""
    if is_local:
        prefix = "LOCAL_"
    
    USER = os.getenv(f"{prefix}DB_USER_ID")
    SERVER = os.getenv(f"{prefix}DB_SERVER") if not is_conteiner else "mssql"
    DATABASE = os.getenv(f"{prefix}DB_NAME") if not db_name else db_name
    PASSWORD = os.getenv(f"{prefix}DB_PASSWORD")
    
    return (
        f"mssql+pyodbc://{USER}:{PASSWORD}@{SERVER}:1433/{DATABASE}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
        f"&TrustServerCertificate=yes"
        f"&Pooling=yes"
    )