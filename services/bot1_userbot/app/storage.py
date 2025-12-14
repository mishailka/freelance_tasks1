from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, Integer, DateTime, select, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


class Base(DeclarativeBase):
    pass


class FallbackMessage(Base):
    __tablename__ = "fallback_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contractor_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    group_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Storage:
    def __init__(self, sqlite_path: str):
        p = Path(sqlite_path)
        if p.parent and str(p.parent) not in (".", ""):
            p.parent.mkdir(parents=True, exist_ok=True)

        # Нормализуем путь (важно для Windows)
        abs_path = p.resolve().as_posix()
        self.engine = create_engine(f"sqlite:///{abs_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)

    def add_fallback_message(self, contractor_id: int, group_id: int, message_id: int) -> None:
        with Session(self.engine) as s:
            s.add(FallbackMessage(contractor_id=contractor_id, group_id=group_id, message_id=message_id))
            s.commit()

    def get_fallback_message(self, contractor_id: int, group_id: int) -> Optional[FallbackMessage]:
        with Session(self.engine) as s:
            stmt = select(FallbackMessage).where(
                FallbackMessage.contractor_id == contractor_id,
                FallbackMessage.group_id == group_id,
            )
            return s.execute(stmt).scalars().first()

    def delete_fallback_message(self, row_id: int) -> None:
        with Session(self.engine) as s:
            s.execute(delete(FallbackMessage).where(FallbackMessage.id == row_id))
            s.commit()
