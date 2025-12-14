import asyncio
import logging

import httpx
from fastapi import FastAPI

from telegram.error import Forbidden

from .config import settings
from .schemas import (
    NotifyNewOrderRequest,
    NotifyPaymentRequest,
    PinOrderDetailsRequest,
    GenericResponse,
)
from .bot_runtime import Bot3

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
log = logging.getLogger("bot3")

bot3 = Bot3()
app = FastAPI(title="Bot3 Notify Bot API", version="1.0.0")


@app.on_event("startup")
async def _startup():
    asyncio.create_task(bot3.start())


@app.on_event("shutdown")
async def _shutdown():
    await bot3.stop()


@app.get("/health")
async def health():
    return {"ok": True}


async def _fallback_via_bot1(contractor_id: int, group_id: int, text: str) -> None:
    url = settings.bot1_api_base.rstrip("/") + "/api/crm/send_fallback_message"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json={"contractor_id": contractor_id, "group_id": group_id, "text": text})
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Bot1 fallback failed: {data}")


@app.post("/api/crm/notify_new_order", response_model=GenericResponse)
async def notify_new_order(req: NotifyNewOrderRequest):
    text = f"У вас новый заказ: {req.order_title}.\nПодробности в чате: {req.group_link}"
    try:
        await bot3.send_new_order(req.contractor_id, req.order_title, req.group_link)
        return GenericResponse(ok=True, result_code="OK")
    except Forbidden:
        # User blocked bot — use userbot to initiate first contact + track join to delete
        try:
            await _fallback_via_bot1(req.contractor_id, req.group_id, text)
            return GenericResponse(ok=True, result_code="OK_FALLBACK_BOT1")
        except Exception as e:
            return GenericResponse(ok=False, result_code="ERROR", error=str(e))
    except Exception as e:
        return GenericResponse(ok=False, result_code="ERROR", error=str(e))


@app.post("/api/crm/notify_payment", response_model=GenericResponse)
async def notify_payment(req: NotifyPaymentRequest):
    try:
        await bot3.send_payment(req.contractor_id, req.amount_rub, req.order_id)
        return GenericResponse(ok=True, result_code="OK")
    except Exception as e:
        return GenericResponse(ok=False, result_code="ERROR", error=str(e))


@app.post("/api/crm/pin_order_details", response_model=GenericResponse)
async def pin_order_details(req: PinOrderDetailsRequest):
    try:
        await bot3.pin_order_details(req.chat_id, req.order_id, title=req.title)
        return GenericResponse(ok=True, result_code="OK")
    except Exception as e:
        return GenericResponse(ok=False, result_code="ERROR", error=str(e))
