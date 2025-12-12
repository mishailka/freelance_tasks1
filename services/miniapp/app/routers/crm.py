from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth_crm import crm_auth
from ..deps import get_db
from ..schemas import OrderUpsertRequest, ContractorUpdateCRMRequest
from .. import crud

router = APIRouter(prefix="/api/crm", tags=["crm"], dependencies=[Depends(crm_auth)])


@router.post("/orders")
def upsert_order(payload: OrderUpsertRequest, db: Session = Depends(get_db)):
    order = crud.upsert_order(db, payload)
    db.commit()
    return {"ok": True, "order_id": order.order_id}


@router.delete("/orders/{order_id}")
def delete_order(order_id: str, db: Session = Depends(get_db)):
    crud.delete_order(db, order_id)
    db.commit()
    return {"ok": True}


@router.put("/contractors/{tg_id}")
def update_contractor(tg_id: int, payload: ContractorUpdateCRMRequest, db: Session = Depends(get_db)):
    c = crud.update_contractor_from_crm(db, tg_id, payload)
    db.commit()
    return {"ok": True, "tg_id": c.tg_id}
