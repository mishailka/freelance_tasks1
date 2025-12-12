import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.error import Forbidden
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from .config import settings

log = logging.getLogger("bot3.runtime")


def make_miniapp_url(order_id: Optional[str] = None) -> str:
    base = settings.miniapp_public_url.rstrip("/")
    if order_id:
        return f"{base}/?order_id={order_id}"
    return f"{base}/"


def make_open_button(order_id: Optional[str] = None, text: str = "Открыть кабинет") -> InlineKeyboardMarkup:
    url = make_miniapp_url(order_id)
    kb = [[InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))]]
    return InlineKeyboardMarkup(kb)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Это корпоративный бот. Откройте личный кабинет подрядчика:",
        reply_markup=make_open_button(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Команды: /start — открыть кабинет.")


class Bot3:
    def __init__(self):
        self.application = Application.builder().token(settings.bot3_token).build()
        self.application.add_handler(CommandHandler("start", start_cmd))
        self.application.add_handler(CommandHandler("help", help_cmd))

    async def start(self) -> None:
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        log.info("Bot3 started polling")

    async def stop(self) -> None:
        try:
            await self.application.updater.stop()
        except Exception:
            pass
        await self.application.stop()
        await self.application.shutdown()
        log.info("Bot3 stopped")

    async def send_new_order(self, contractor_id: int, order_title: str, group_link: str) -> None:
        text = f"У вас новый заказ: {order_title}.\nПодробности в чате: {group_link}"
        await self.application.bot.send_message(chat_id=contractor_id, text=text)

    async def send_payment(self, contractor_id: int, amount_rub: int, order_id: str) -> None:
        text = f"Мы отправили вам {amount_rub} руб."
        await self.application.bot.send_message(
            chat_id=contractor_id,
            text=text,
            reply_markup=make_open_button(order_id, text="Открыть мини‑приложение"),
        )

    async def pin_order_details(self, chat_id: int, order_id: str, title: Optional[str] = None) -> int:
        caption = "Детали заказа"
        if title:
            caption = f"Детали заказа: {title}"
        msg = await self.application.bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=make_open_button(order_id, text="Детали заказа"),
        )
        try:
            await self.application.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id, disable_notification=True)
        except Exception as e:
            log.warning("Failed to pin message in %s: %s", chat_id, e)
        return msg.message_id
