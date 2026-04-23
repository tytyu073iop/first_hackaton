# filepath: backend/models.py
import os
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    UniqueConstraint, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./game.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Partner(Base):
    __tablename__ = "partners"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hex_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    mcc_code = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    cashback_percent = Column(Float, nullable=False, default=0.0)


class PlayerProgress(Base):
    __tablename__ = "player_progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String, nullable=False, index=True)
    hex_id = Column(String, nullable=False, index=True)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    quest_type = Column(String, nullable=False, default="single_transaction")
    __table_args__ = (
        UniqueConstraint("player_id", "hex_id", name="uq_player_hex"),
    )


class Quest(Base):
    __tablename__ = "quests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String, nullable=False, index=True)
    hex_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    target_value = Column(Integer, nullable=False, default=1)
    current_value = Column(Integer, nullable=False, default=0)
    mcc_filter = Column(String, nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PendingTransaction(Base):
    __tablename__ = "pending_transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String, nullable=False, index=True)
    partner_id = Column(Integer, nullable=True, index=True)  # FK к Partner.id (опц. для совместимости)
    partner_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    mcc_code = Column(String, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    consumed_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)  # UUID, он же player_id
    name = Column(String, nullable=False)
    recovery_code = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint("player_id", "code", name="uq_player_code"),
    )


class Reward(Base):
    """Промокод / бонус, выданный за ачивку. Имеет срок годности и используется один раз."""
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String, nullable=False, index=True)
    source_code = Column(String, nullable=False)  # код ачивки, за которую выдано
    code = Column(String, nullable=False, index=True)  # промо-код для показа пользователю
    title = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    reward_type = Column(String, nullable=False, default="bonus")  # cashback_boost | discount | bonus_points | free_unlock
    value = Column(Float, nullable=False, default=0.0)  # % или сумма — зависит от reward_type
    scope = Column(String, nullable=True)  # категория для cashback_boost (restaurant/grocery/...)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)
