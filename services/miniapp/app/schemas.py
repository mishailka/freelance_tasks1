from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


StageDisplayMode = Literal["hours", "sums"]


class StageIn(BaseModel):
    date: Optional[datetime] = None
    hours: Optional[int] = None
    amount: Optional[int] = None
    comment: Optional[str] = None
    contractor_id: Optional[int] = None


class FileIn(BaseModel):
    name: Optional[str] = None
    url: str


class PropertyIn(BaseModel):
    name: str
    quantity: int = 1
    comment: Optional[str] = None
    contractor_id: Optional[int] = None


class OrderUpsertRequest(BaseModel):
    order_id: str = Field(..., description="Айди заказа")
    chat_link: Optional[str] = Field(None, description="Ссылка на чат")
    tz_text: Optional[str] = Field(None, description="ТЗ (текст)")
    terms_text: Optional[str] = Field(None, description="Условия работы")

    contractors: List[int] = Field(default_factory=list, description="tg_id подрядчиков")
    stages_display_mode: StageDisplayMode = "hours"
    stages_readonly: bool = False

    stages: List[StageIn] = Field(default_factory=list)
    files: List[FileIn] = Field(default_factory=list)
    properties: List[PropertyIn] = Field(default_factory=list)


class ContractorUpdateCRMRequest(BaseModel):
    advance_amount: Optional[int] = None
    contact_info: Optional[str] = None
    payment_info: Optional[str] = None


class OrderOut(BaseModel):
    order_id: str
    chat_link: Optional[str]
    tz_text: Optional[str]
    terms_text: Optional[str]
    stages_display_mode: StageDisplayMode
    stages_readonly: bool


class StageOut(BaseModel):
    id: int
    date: datetime
    hours: Optional[int]
    amount: Optional[int]
    comment: Optional[str]
    contractor_id: int


class PropertyOut(BaseModel):
    id: int
    name: str
    quantity: int
    comment: Optional[str]


class FileOut(BaseModel):
    id: int
    name: Optional[str]
    url: str


class ContractorOut(BaseModel):
    tg_id: int
    advance_amount: int
    contact_info: Optional[str]
    payment_info: Optional[str]


class MeResponse(BaseModel):
    contractor: ContractorOut
    orders: List[OrderOut]


class OrderDetailsResponse(BaseModel):
    order: OrderOut
    contractor: ContractorOut
    stages: List[StageOut]
    files: List[FileOut]
    properties: List[PropertyOut]


class AddStageRequest(BaseModel):
    hours: int = Field(..., ge=0)
    comment: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    contact_info: Optional[str] = None
    payment_info: Optional[str] = None
