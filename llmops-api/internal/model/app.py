import uuid
from email.policy import default

from sqlalchemy import (
    Column,
    UUID,
    String, Text, DateTime, PrimaryKeyConstraint, Index, text
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

    id = Column(UUID, server_default=text("uuid_generate_v4()"), nullable=False)
    account_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default="''::character varying")
    icon = Column(String(255), nullable=False, server_default="''::character varying")
    description = Column(Text, nullable=False, server_default="''::text")
    status=Column(String(255), nullable=False, server_default="''::character varying")
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
    updated_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"), server_onupdate=text("CURRENT_TIMESTAMP(0)"))


class AppDatasetJoin(db.Model):
    """应用知识库关联表模型"""
    __tablename__ = "app_dataset_join"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_dataset_join_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    app_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
