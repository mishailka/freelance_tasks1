from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..auth import get_current_contractor_id
from ..deps import get_db
from .. import crud, models
from ..schemas import (
    MeResponse,
    ContractorOut,
    OrderOut,
    OrderDetailsResponse,
    StageOut,
    FileOut,
    PropertyOut,
    AddStageRequest,
    UpdateProfileRequest,
)

router = APIRouter(prefix="/api/app", tags=["app"])


def _contractor_out(c: models.Contractor) -> ContractorOut:
    return ContractorOut(
        tg_id=c.tg_id,
        advance_amount=c.advance_amount,
        contact_info=c.contact_info,
        payment_info=c.payment_info,
    )


def _order_out(o: models.Order) -> OrderOut:
    return OrderOut(
        order_id=o.order_id,
        chat_link=o.chat_link,
        tz_text=o.tz_text,
        terms_text=o.terms_text,
        stages_display_mode=o.stages_display_mode,  # type: ignore
        stages_readonly=o.stages_readonly,
    )


@router.get("/me", response_model=MeResponse)
def me(
    contractor_id: int = Depends(get_current_contractor_id),
    db: Session = Depends(get_db),
):
    c = crud.get_or_create_contractor(db, contractor_id)
    orders = crud.list_orders_for_contractor(db, contractor_id)
    return MeResponse(contractor=_contractor_out(c), orders=[_order_out(o) for o in orders])


@router.get("/orders/{order_id}", response_model=OrderDetailsResponse)
def order_details(
    order_id: str,
    contractor_id: int = Depends(get_current_contractor_id),
    db: Session = Depends(get_db),
):
    order = crud.get_order_for_contractor(db, order_id, contractor_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not assigned")

    c = crud.get_or_create_contractor(db, contractor_id)

    stages = (
        db.execute(
            select(models.Stage)
            .where(models.Stage.order_id == order_id)
            .order_by(models.Stage.date.desc())
        )
        .scalars()
        .all()
    )
    files = (
        db.execute(select(models.OrderFile).where(models.OrderFile.order_id == order_id))
        .scalars()
        .all()
    )
    props = (
        db.execute(
            select(models.PropertyItem)
            .where(models.PropertyItem.order_id == order_id)
            .where((models.PropertyItem.contractor_id == None) | (models.PropertyItem.contractor_id == contractor_id))  # noqa: E711
            .order_by(models.PropertyItem.id.desc())
        )
        .scalars()
        .all()
    )

    return OrderDetailsResponse(
        order=_order_out(order),
        contractor=_contractor_out(c),
        stages=[
            StageOut(
                id=s.id,
                date=s.date,
                hours=s.hours,
                amount=s.amount,
                comment=s.comment,
                contractor_id=s.contractor_id,
            )
            for s in stages
        ],
        files=[FileOut(id=f.id, name=f.name, url=f.url) for f in files],
        properties=[PropertyOut(id=p.id, name=p.name, quantity=p.quantity, comment=p.comment) for p in props],
    )


@router.post("/orders/{order_id}/stages")
def add_stage(
    order_id: str,
    payload: AddStageRequest,
    contractor_id: int = Depends(get_current_contractor_id),
    db: Session = Depends(get_db),
):
    order = crud.get_order_for_contractor(db, order_id, contractor_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not assigned")
    if order.stages_readonly:
        raise HTTPException(status_code=403, detail="Stages are readonly for this order")

    stage = models.Stage(
        order_id=order_id,
        contractor_id=contractor_id,
        date=datetime.utcnow(),
        hours=payload.hours,
        amount=None,
        comment=payload.comment,
    )
    db.add(stage)
    db.commit()
    return {"ok": True, "stage_id": stage.id}


@router.put("/profile")
def update_profile(
    payload: UpdateProfileRequest,
    contractor_id: int = Depends(get_current_contractor_id),
    db: Session = Depends(get_db),
):
    c = crud.get_or_create_contractor(db, contractor_id)
    if payload.contact_info is not None:
        c.contact_info = payload.contact_info
    if payload.payment_info is not None:
        c.payment_info = payload.payment_info
    db.commit()
    return {"ok": True}
