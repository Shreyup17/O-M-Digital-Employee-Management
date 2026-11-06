from sqlalchemy import Column, Integer, String, Boolean, Text
from database import Base


class OMAccount(Base):
    __tablename__ = "om_accounts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True)  # Unique ID
    full_name = Column(String)  # Personnel name
    department = Column(String)  # For filtering
    password = Column(String)  # Hashed password
    is_active = Column(Boolean, default=True)  # For "freezing"


class IssueRecord(Base):
    __tablename__ = "issue_records"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text)  # AI couldn't answer [cite: 20]
    is_unanswered = Column(Boolean, default=True)  # Tracking status
    human_solution = Column(Text, nullable=True)  # Manual intervention