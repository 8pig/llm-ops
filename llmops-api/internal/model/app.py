import uuid
from email.policy import default

from sqlalchemy import (
    Column,
    UUID,
    String, Text, DateTime, PrimaryKeyConstraint, Index
)
from datetime import datetime

from internal.extension.database_extension import db

class App(db.Model):
    """ai应用基础模型类"""
    __tablename__ = "app"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("idx_app_account_id", "account_id")
    )

    id = Column(UUID, default=uuid.uuid4, nullable=False)
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, default="")
    icon = Column(String(255), nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

