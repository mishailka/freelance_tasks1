from fastapi import Header, HTTPException
from .config import settings


def crm_auth(x_crm_api_key: str = Header(..., alias="X-CRM-API-Key")) -> None:
    if x_crm_api_key != settings.crm_api_key:
        raise HTTPException(status_code=401, detail="Invalid CRM API key")
