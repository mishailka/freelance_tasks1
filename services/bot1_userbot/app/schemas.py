from pydantic import BaseModel, Field
from typing import List, Optional


class CreateGroupRequest(BaseModel):
    order_id: str
    title: str
    description: Optional[str] = None
    icon_base64: Optional[str] = None

    curator_id: int
    curator_label: str

    contractor_ids: List[int]

    bot2_username: Optional[str] = None
    bot3_username: Optional[str] = None


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
