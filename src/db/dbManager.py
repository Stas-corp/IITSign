from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from src.db.schema import SignatureFile, Base
from src.db.config import connection_string

class DatabaseManager:
    def __init__(
        self, 
        db_name: str = None,
        is_local_conection: bool = False,
        is_conteiner: bool = False
    ):
        """
        Инициализация менеджера базы данных
        
        Args:
            db_name: имя таблицы
            is_local_conection: показатель на подключение к локальной базе,
                                тянет данные из .env
        """
        self.database_url = connection_string(
            db_name=db_name,
            is_local=is_local_conection,
            is_conteiner=is_conteiner
        )
        print("*"*50, "\n", self.database_url, "\n", "*"*50)
        self.engine = create_engine(
            self.database_url,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True
        )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine, autoflush=False)
        self.session = scoped_session(Session)
    
    
    def add_files_for_signing(self, file_paths, is_checking: bool = True):
        """
        Функция для проверки и записи всех файлов для подписи в таблицу. 
        По умолчанию вызывает ошибку, если записи нет в таблице
        
        Args:
            file_paths: список путей к файлам
            is_checking: True - вызвать исключение, если записи в таблице нет
        
        Returns:
            int: количество добавленных файлов
        """
        added_count = 0
        missing_records = []
        
        for file_path in file_paths:
            path_obj = Path(file_path)
            filename = path_obj.name
            parent_folder = path_obj.parent.name
            
            formatted_path = f"{parent_folder}/{filename}"
            
            existing_file = self.session.query(SignatureFile).filter_by(
                RelativePath=formatted_path
            ).first()
            
            # Если записи нет, добавляем новую
            if not existing_file:
                if is_checking:
                    missing_records.append(formatted_path)
                    continue
                new_file = SignatureFile(
                    Name=filename,
                    RelativePath=formatted_path,
                    IsSigned=False
                )
                self.session.add(new_file)
                added_count += 1
        
        if len(missing_records) > 0:
            raise ValueError(f"Records that are missing from the table: {missing_records}")
        try:
            self.session.commit()
            return added_count
        except Exception as e:
            self.session.rollback()
            raise e
    
    
    def mark_file_as_signed(self, file_path):
        """
        Функция для изменения статуса файла на подписанный (True)
        
        Args:
            file_path: путь к файлу в формате "родительская_папка/имя_файла"
        
        Returns:
            bool: True если файл найден и обновлен, False если не найден
        """
        file_record = self.session.query(SignatureFile).filter_by(
            RelativePath=file_path
        ).first()
        
        if file_record:
            file_record.IsSigned = True
            try:
                self.session.commit()
                return True
            except Exception as e:
                self.session.rollback()
                raise e
        
        return False
    
    
    def mark_multiple_files_as_signed(self, file_paths):
        """
        Функция для массового обновления статуса нескольких файлов
        
        Args:
            file_paths: список путей к файлам
        
        Returns:
            int: количество обновленных файлов
        """
        updated_count = 0
        
        for file_path in file_paths:
            if self.mark_file_as_signed(file_path):
                updated_count += 1
        
        return updated_count
    
    
    def get_unsigned_files(self):
        """
        Получить список неподписанных файлов
        
        Returns:
            list: список объектов SignatureFile с is_signed=False
        """
        return self.session.query(SignatureFile).filter_by(IsSigned=False).all()
    
    
    def get_signed_files(self):
        """
        Получить список подписанных файлов
        
        Returns:
            list: список объектов SignatureFile с is_signed=True
        """
        return self.session.query(SignatureFile).filter_by(IsSigned=True).all()
    
    
    def get_all_files(self):
        """
        Получить все файлы из базы данных
        
        Returns:
            list: список всех объектов SignatureFile
        """
        return self.session.query(SignatureFile).all()
    
    
    def close(self):
        self.session.close()