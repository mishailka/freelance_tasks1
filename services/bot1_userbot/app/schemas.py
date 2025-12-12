from pydantic import BaseModel, Field
from typing import List, Optional


class CreateGroupRequest(BaseModel):
    order_id: str = Field(..., description="ID заказа (для логов/удобства)")
    title: str
    description: Optional[str] = None
    icon_base64: Optional[str] = Field(
        None,
        description="Иконка группы в base64 (PNG/JPG). Можно null, если не нужно менять фото.",
    )

    curator_id: int
    curator_label: str = Field(..., description="Custom title для куратора (label)")

    contractor_ids: List[int] = Field(default_factory=list)

    bot2_username: str = Field(..., description="username Bot2 без @")
    bot3_username: str = Field(..., description="username Bot3 без @")


class CreateGroupResponse(BaseModel):
    ok: bool
    result_code: str
    group_id: Optional[int] = None
    group_link: Optional[str] = None
    error: Optional[str] = None


class RemoveContractorRequest(BaseModel):
    chat_id: int
    contractor_id: int


class SendFallbackMessageRequest(BaseModel):
    contractor_id: int
    group_id: int
    text: str


class GenericResponse(BaseModel):
    ok: bool
    result_code: str
    error: Optional[str] = None
