from sqlalchemy import (
    Column, 
    Integer, 
    Boolean,
    BigInteger,
    DateTime,
    NCHAR,
    func
)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class SignatureFile(Base):
    __tablename__ = "files"
    __table_args__ = {"extend_existing": True}
    
    Id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    Name = Column(NCHAR(256, collation="Cyrillic_General_CI_AS"), nullable=False)
    RelativePath = Column(NCHAR(256, collation="Cyrillic_General_CI_AS"), nullable=False)
    ClaimId = Column(BigInteger, nullable=True)
    State = Column(Integer, nullable=True)
    ECourtResponceSign = Column(NCHAR(256, collation="Cyrillic_General_CI_AS"), nullable=True)
    CreatedAt = Column(DateTime, nullable=True, server_default=func.sysdatetime())
    UpdatedAt = Column(DateTime, nullable=True,
                       server_default=func.sysdatetime(),
                       onupdate=func.sysdatetime())
    IsSigned = Column(Boolean, nullable=False, server_default="0")
    ECourtResponceFile = Column(NCHAR(256, collation="Cyrillic_General_CI_AS"), nullable=True)
    IsSended = Column(Boolean, nullable=True, server_default="0")
    ECourtFileId = Column(NCHAR(256, collation="Cyrillic_General_CI_AS"), nullable=True)
    ECourtFileLink = Column(NCHAR(256, collation="Cyrillic_General_CI_AS"), nullable=True)
    ECourtSignFileId = Column(NCHAR(256, collation="Cyrillic_General_CI_AS"), nullable=True)
    ECourtSignFileLink = Column(NCHAR(256, collation="Cyrillic_General_CI_AS"), nullable=True)