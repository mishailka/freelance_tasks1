import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import settings
from .schemas import (
    CreateGroupRequest,
    CreateGroupResponse,
    RemoveContractorRequest,
    SendFallbackMessageRequest,
    GenericResponse,
)
from .storage import Storage
from .telegram_client import TelegramUserbot

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
log = logging.getLogger("bot1")

storage = Storage(settings.bot1_db_path)
tg = TelegramUserbot(storage=storage)

app = FastAPI(title="Bot1 Userbot API", version="1.0.0")


@app.on_event("startup")
async def _startup():
    await tg.start()


@app.on_event("shutdown")
async def _shutdown():
    await tg.stop()


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/api/crm/create_group", response_model=CreateGroupResponse)
async def create_group(req: CreateGroupRequest):
    res = await tg.create_and_setup_group(
        title=req.title,
        description=req.description,
        icon_base64=req.icon_base64,
        curator_id=req.curator_id,
        curator_label=req.curator_label,
        contractor_ids=req.contractor_ids,
        bot2_username=req.bot2_username,
        bot3_username=req.bot3_username,
    )
    if res.ok:
        return CreateGroupResponse(ok=True, result_code="OK", group_id=res.group_id, group_link=res.group_link)
    return CreateGroupResponse(ok=False, result_code="ERROR", error=res.error)


@app.post("/api/crm/remove_contractor", response_model=GenericResponse)
async def remove_contractor(req: RemoveContractorRequest):
    try:
        await tg.remove_contractor(chat_id=req.chat_id, contractor_id=req.contractor_id)
        return GenericResponse(ok=True, result_code="OK")
    except Exception as e:
        return GenericResponse(ok=False, result_code="ERROR", error=str(e))


@app.post("/api/crm/send_fallback_message", response_model=GenericResponse)
async def send_fallback_message(req: SendFallbackMessageRequest):
    try:
        await tg.send_fallback_message_and_track(
            contractor_id=req.contractor_id,
            group_id=req.group_id,
            text=req.text,
        )
        return GenericResponse(ok=True, result_code="OK")
    except Exception as e:
        return GenericResponse(ok=False, result_code="ERROR", error=str(e))
