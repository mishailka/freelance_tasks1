from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from . import models
from .schemas import OrderUpsertRequest, ContractorUpdateCRMRequest


def get_or_create_contractor(db: Session, tg_id: int) -> models.Contractor:
    c = db.get(models.Contractor, tg_id)
    if c:
        return c
    c = models.Contractor(tg_id=tg_id)
    db.add(c)
    db.flush()
    return c


def upsert_order(db: Session, payload: OrderUpsertRequest) -> models.Order:
    order = db.get(models.Order, payload.order_id)
    if not order:
        order = models.Order(order_id=payload.order_id)
        db.add(order)

    order.chat_link = payload.chat_link
    order.tz_text = payload.tz_text
    order.terms_text = payload.terms_text
    order.stages_display_mode = payload.stages_display_mode
    order.stages_readonly = payload.stages_readonly

    # contractors association
    # ensure contractors exist
    contractor_ids = list(dict.fromkeys(payload.contractors))  # unique keep order
    for cid in contractor_ids:
        get_or_create_contractor(db, cid)

    # replace associations
    db.execute(delete(models.OrderContractor).where(models.OrderContractor.order_id == order.order_id))
    for cid in contractor_ids:
        db.add(models.OrderContractor(order_id=order.order_id, contractor_id=cid))

    # replace files
    db.execute(delete(models.OrderFile).where(models.OrderFile.order_id == order.order_id))
    for f in payload.files:
        db.add(models.OrderFile(order_id=order.order_id, name=f.name, url=f.url))

    # replace properties
    db.execute(delete(models.PropertyItem).where(models.PropertyItem.order_id == order.order_id))
    for p in payload.properties:
        db.add(
            models.PropertyItem(
                order_id=order.order_id,
                contractor_id=p.contractor_id,
                name=p.name,
                quantity=p.quantity,
                comment=p.comment,
            )
        )

    # replace stages if provided (CRM may send full list)
    db.execute(delete(models.Stage).where(models.Stage.order_id == order.order_id))
    for s in payload.stages:
        dt = s.date or datetime.utcnow()
        contractor_id = s.contractor_id or (contractor_ids[0] if contractor_ids else 0)
        if contractor_id:
            get_or_create_contractor(db, contractor_id)
        db.add(
            models.Stage(
                order_id=order.order_id,
                contractor_id=contractor_id,
                date=dt,
                hours=s.hours,
                amount=s.amount,
                comment=s.comment,
            )
        )

    db.flush()
    return order


def delete_order(db: Session, order_id: str) -> None:
    order = db.get(models.Order, order_id)
    if order:
        db.delete(order)
        db.flush()


def update_contractor_from_crm(db: Session, tg_id: int, payload: ContractorUpdateCRMRequest) -> models.Contractor:
    c = get_or_create_contractor(db, tg_id)
    if payload.advance_amount is not None:
        c.advance_amount = payload.advance_amount
    if payload.contact_info is not None:
        c.contact_info = payload.contact_info
    if payload.payment_info is not None:
        c.payment_info = payload.payment_info
    db.flush()
    return c


def list_orders_for_contractor(db: Session, tg_id: int) -> List[models.Order]:
    stmt = (
        select(models.Order)
        .join(models.OrderContractor, models.Order.order_id == models.OrderContractor.order_id)
        .where(models.OrderContractor.contractor_id == tg_id)
        .order_by(models.Order.order_id)
    )
    return list(db.execute(stmt).scalars().all())


def get_order_for_contractor(db: Session, order_id: str, tg_id: int) -> Optional[models.Order]:
    stmt = (
        select(models.Order)
        .join(models.OrderContractor, models.Order.order_id == models.OrderContractor.order_id)
        .where(models.Order.order_id == order_id, models.OrderContractor.contractor_id == tg_id)
    )
    return db.execute(stmt).scalars().first()
