from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Contractor(Base):
    __tablename__ = "contractors"

    tg_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    advance_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contact_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    orders: Mapped[List["OrderContractor"]] = relationship(back_populates="contractor", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    chat_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tz_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    terms_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # how to display stages: hours/sums
    stages_display_mode: Mapped[str] = mapped_column(String(16), default="hours", nullable=False)
    stages_readonly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    contractors: Mapped[List["OrderContractor"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    stages: Mapped[List["Stage"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    files: Mapped[List["OrderFile"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    properties: Mapped[List["PropertyItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderContractor(Base):
    __tablename__ = "order_contractors"
    __table_args__ = (UniqueConstraint("order_id", "contractor_id", name="uq_order_contractor"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"))
    contractor_id: Mapped[int] = mapped_column(ForeignKey("contractors.tg_id", ondelete="CASCADE"))

    order: Mapped["Order"] = relationship(back_populates="contractors")
    contractor: Mapped["Contractor"] = relationship(back_populates="orders")


class Stage(Base):
    __tablename__ = "stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"), index=True)
    contractor_id: Mapped[int] = mapped_column(ForeignKey("contractors.tg_id", ondelete="CASCADE"), index=True)

    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="stages")


class OrderFile(Base):
    __tablename__ = "order_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"), index=True)
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="files")


class PropertyItem(Base):
    __tablename__ = "property_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"), index=True)
    contractor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contractors.tg_id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="properties")
