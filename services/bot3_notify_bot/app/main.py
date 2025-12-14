import asyncio
import logging
from urllib.parse import quote

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from telegram.error import Forbidden

from .bot_runtime import Bot3
from .config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
log = logging.getLogger("bot3")

bot3 = Bot3()
app = FastAPI(title="Bot3 Web UI", version="2.0.0")


@app.on_event("startup")
async def _startup():
    # Run bot polling in background task
    asyncio.create_task(bot3.start())


@app.on_event("shutdown")
async def _shutdown():
    await bot3.stop()


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "bot3_web_ui",
        "miniapp_public_url": settings.miniapp_public_url,
    }


def _page(message: str | None = None, error: str | None = None) -> str:
    msg_html = ""
    if message:
        msg_html = f"""
        <div class='card ok'>
          <div class='title'>Готово</div>
          <div class='body'>{message}</div>
        </div>
        """
    if error:
        msg_html = f"""
        <div class='card err'>
          <div class='title'>Ошибка</div>
          <div class='body'>{error}</div>
        </div>
        """

    return f"""<!doctype html>
<html lang='ru'>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <title>Bot3 Web UI</title>
    <style>
      :root {{ --bg:#0b0f19; --card:#111827; --text:#e5e7eb; --muted:#9ca3af; --border:#1f2937; }}
      body {{ background:var(--bg); color:var(--text); font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial; margin:0; }}
      .wrap {{ max-width: 980px; margin: 0 auto; padding: 24px; }}
      h1 {{ font-size: 22px; margin: 0 0 6px; }}
      .sub {{ color: var(--muted); margin: 0 0 18px; }}
      .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
      @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
      .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 14px; }}
      .card.ok {{ border-color: #065f46; }}
      .card.err {{ border-color: #991b1b; }}
      .title {{ font-weight: 700; margin-bottom: 8px; }}
      .body {{ color: var(--text); line-height: 1.45; white-space: pre-wrap; }}
      label {{ display:block; font-size: 13px; color: var(--muted); margin: 10px 0 6px; }}
      input, textarea {{ width: 100%; box-sizing: border-box; border-radius: 10px; border: 1px solid var(--border); background: #0b1220; color: var(--text); padding: 10px 12px; }}
      textarea {{ min-height: 96px; resize: vertical; }}
      .row {{ display:flex; gap: 10px; }}
      .row > div {{ flex: 1; }}
      button {{ margin-top: 12px; background: #2563eb; border: 0; color: white; padding: 10px 12px; border-radius: 10px; font-weight: 600; cursor: pointer; }}
      button:hover {{ filter: brightness(1.05); }}
      .hint {{ color: var(--muted); font-size: 12px; margin-top: 8px; }}
      .topbar {{ display:flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 12px; }}
      .pill {{ display:inline-block; padding: 6px 10px; border: 1px solid var(--border); border-radius: 999px; color: var(--muted); font-size: 12px; }}
      a {{ color: #93c5fd; text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      hr {{ border:0; border-top: 1px solid var(--border); margin: 14px 0; }}
    </style>
  </head>
  <body>
    <div class='wrap'>
      <div class='topbar'>
        <div>
          <h1>Bot3 Web UI</h1>
          <p class='sub'>Сервис не связан с CRM — только ручные действия через веб-формы.</p>
        </div>
        <div class='pill'>MiniApp: {settings.miniapp_public_url}</div>
      </div>

      {msg_html}

      <div class='grid'>
        <div class='card'>
          <div class='title'>Отправить «Новый заказ»</div>
          <form method='post' action='/ui/send/new-order'>
            <label>contractor_id (TG user id)</label>
            <input name='contractor_id' type='number' required />

            <label>order_title</label>
            <input name='order_title' type='text' value='TEST-ORDER' required />

            <label>group_link (инвайт/ссылка на чат)</label>
            <input name='group_link' type='text' value='https://t.me/...' required />

            <button type='submit'>Отправить</button>
            <div class='hint'>Если пользователь не нажимал /start у бота — Telegram вернёт Forbidden.</div>
          </form>
        </div>

        <div class='card'>
          <div class='title'>Отправить «Оплата» + кнопка мини-аппа</div>
          <form method='post' action='/ui/send/payment'>
            <div class='row'>
              <div>
                <label>contractor_id</label>
                <input name='contractor_id' type='number' required />
              </div>
              <div>
                <label>amount_rub</label>
                <input name='amount_rub' type='number' value='1000' min='0' required />
              </div>
            </div>

            <label>order_id (пойдет в miniapp URL)</label>
            <input name='order_id' type='text' value='TEST-001' required />

            <button type='submit'>Отправить</button>
          </form>
        </div>

        <div class='card'>
          <div class='title'>Закрепить «Детали заказа» в группе</div>
          <form method='post' action='/ui/chat/pin-order-details'>
            <label>chat_id (ID группы вида -100...)</label>
            <input name='chat_id' type='number' required />

            <label>order_id</label>
            <input name='order_id' type='text' value='TEST-001' required />

            <label>title (опционально)</label>
            <input name='title' type='text' value='TEST-ORDER' />

            <button type='submit'>Отправить и закрепить</button>
            <div class='hint'>Бот должен быть админом группы с правом «Закреплять сообщения».</div>
          </form>
        </div>

        <div class='card'>
          <div class='title'>Отправить произвольный текст</div>
          <form method='post' action='/ui/send/raw'>
            <label>contractor_id</label>
            <input name='contractor_id' type='number' required />

            <label>text</label>
            <textarea name='text' required>Тестовое сообщение</textarea>

            <label>order_id (если нужно добавить кнопку мини-аппа; пусто = без кнопки)</label>
            <input name='order_id' type='text' placeholder='например TEST-001' />

            <button type='submit'>Отправить</button>
          </form>
        </div>
      </div>

      <hr />
      <div class='hint'>Полезное: <a href='/docs' target='_blank'>OpenAPI /docs</a> • <a href='/health' target='_blank'>/health</a></div>
    </div>
  </body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index(msg: str | None = None, err: str | None = None):
    return HTMLResponse(_page(message=msg, error=err))


@app.post("/ui/send/new-order")
async def ui_send_new_order(
    contractor_id: int = Form(...),
    order_title: str = Form(...),
    group_link: str = Form(...),
):
    try:
        await bot3.send_new_order(contractor_id, order_title, group_link)
        return RedirectResponse(url=f"/?msg={quote('Сообщение отправлено')}", status_code=303)
    except Forbidden:
        return RedirectResponse(
            url=f"/?err={quote('Forbidden: пользователь не запускал бота или заблокировал его. Попросите подрядчика открыть чат с ботом и нажать /start.')}",
            status_code=303,
        )
    except Exception as e:
        log.exception("send_new_order failed")
        return RedirectResponse(url=f"/?err={quote(str(e))}", status_code=303)


@app.post("/ui/send/payment")
async def ui_send_payment(
    contractor_id: int = Form(...),
    amount_rub: int = Form(...),
    order_id: str = Form(...),
):
    try:
        await bot3.send_payment(contractor_id, amount_rub, order_id)
        return RedirectResponse(url=f"/?msg={quote('Оплата отправлена (со ссылкой на мини-апп)')}", status_code=303)
    except Forbidden:
        return RedirectResponse(
            url=f"/?err={quote('Forbidden: пользователь не запускал бота или заблокировал его. Попросите подрядчика открыть чат с ботом и нажать /start.')}",
            status_code=303,
        )
    except Exception as e:
        log.exception("send_payment failed")
        return RedirectResponse(url=f"/?err={quote(str(e))}", status_code=303)


@app.post("/ui/chat/pin-order-details")
async def ui_pin_order_details(
    chat_id: int = Form(...),
    order_id: str = Form(...),
    title: str = Form(""),
):
    try:
        await bot3.pin_order_details(chat_id, order_id, title=title or None)
        return RedirectResponse(
            url=f"/?msg={quote('Сообщение отправлено и (если было возможно) закреплено')}",
            status_code=303,
        )
    except Exception as e:
        log.exception("pin_order_details failed")
        return RedirectResponse(url=f"/?err={quote(str(e))}", status_code=303)


@app.post("/ui/send/raw")
async def ui_send_raw(
    contractor_id: int = Form(...),
    text: str = Form(...),
    order_id: str = Form(""),
):
    try:
        await bot3.send_raw(contractor_id, text, order_id=order_id or None)
        return RedirectResponse(url=f"/?msg={quote('Сообщение отправлено')}", status_code=303)
    except Forbidden:
        return RedirectResponse(
            url=f"/?err={quote('Forbidden: пользователь не запускал бота или заблокировал его. Попросите подрядчика открыть чат с ботом и нажать /start.')}",
            status_code=303,
        )
    except Exception as e:
        log.exception("send_raw failed")
        return RedirectResponse(url=f"/?err={quote(str(e))}", status_code=303)
