from pydantic import BaseModel
from typing import Optional


class NotifyNewOrderRequest(BaseModel):
    contractor_id: int
    order_title: str
    group_link: str
    group_id: int


class NotifyPaymentRequest(BaseModel):
    contractor_id: int
    amount_rub: int
    order_id: str


class PinOrderDetailsRequest(BaseModel):
    chat_id: int
    order_id: str
    title: Optional[str] = None


class GenericResponse(BaseModel):
    ok: bool
    result_code: str
    error: Optional[str] = None
