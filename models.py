from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

STATUSES = ["в работе ⚙️", "выполнено ✅", "отклонено ❌"]

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    text = Column(String, nullable=False)
    media = Column(JSON, nullable=True)  # новое поле для фото/видео/документов
    status = Column(String, default="новый 🆕")
    created_at = Column(DateTime, default=datetime.utcnow)
