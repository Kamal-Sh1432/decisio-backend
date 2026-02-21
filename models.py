from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
from database import Base

class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    industry = Column(String, nullable=True)
    ai_output = Column(JSON, nullable=True)
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=datetime.utcnow)