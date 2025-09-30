from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin' or 'user'

class Certificate(Base):
    __tablename__ = "certificates"
    cert_id = Column(String(64), primary_key=True)
    student_name = Column(String(100))
    roll_number = Column(String(50))
    course = Column(String(100))
    institution = Column(String(150))
    year_of_passing = Column(Integer)
    marks_percentage = Column(Float)

class VerificationLog(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    cert_id = Column(String(64))
    extracted_text = Column(Text)
    detected_cert_id = Column(String(64))
    result = Column(String(20))  # valid / fake / not_found / not_detected
    uploaded_filename = Column(String(200))
    verifier = Column(String(100))  # who uploaded
    timestamp = Column(DateTime, default=datetime.utcnow)
