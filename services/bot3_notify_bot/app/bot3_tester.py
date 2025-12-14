#!/usr/bin/env python3
"""Консольный тестер для Bot3 Web UI.

Этот сервис теперь не принимает JSON-команды от CRM. Тестер дергает веб-эндпоинты
(/ui/...) через form-data (application/x-www-form-urlencoded).
"""

import argparse
import re
import sys
from typing import Optional

try:
    import httpx
except ImportError:
    print("Не найден модуль httpx. Установи: pip install httpx", file=sys.stderr)
    sys.exit(1)


def _prompt(text: str, default: Optional[str] = None) -> str:
    if default is None:
        return input(f"{text}: ").strip()
    s = input(f"{text} [{default}]: ").strip()
    return s if s else default


def _prompt_int(text: str, default: Optional[int] = None) -> int:
    while True:
        s = _prompt(text, str(default) if default is not None else None)
        try:
            return int(s)
        except ValueError:
            print("Введите целое число.")


def _extract_flash(html: str) -> str:
    """Достает текст блока 'Готово/Ошибка' из HTML страницы."""
    m = re.search(r"<div class='card (ok|err)'>.*?<div class='body'>(.*?)</div>", html, re.S)
    if not m:
        return "(ответ получен, но не удалось распарсить сообщение из HTML)"
    body = m.group(2)
    # грубо убрать теги
    body = re.sub(r"<.*?>", "", body)
    return body.strip()


def action_health(client: httpx.Client, base: str) -> None:
    r = client.get(f"{base}/health", timeout=30)
    print(f"HTTP {r.status_code}\n{r.text}")


def action_open_ui(base: str) -> None:
    print(f"Открой в браузере: {base}/")


def action_notify_new_order(client: httpx.Client, base: str) -> None:
    print("\n=== UI: SEND NEW ORDER ===")
    contractor_id = _prompt_int("contractor_id (TG user id подрядчика)")
    order_title = _prompt("order_title", "TEST-ORDER")
    group_link = _prompt("group_link (ссылка на чат)", "https://t.me/...")

    r = client.post(
        f"{base}/ui/send/new-order",
        data={"contractor_id": contractor_id, "order_title": order_title, "group_link": group_link},
        timeout=60,
        follow_redirects=True,
    )
    print(f"HTTP {r.status_code}\n{_extract_flash(r.text)}")


def action_notify_payment(client: httpx.Client, base: str) -> None:
    print("\n=== UI: SEND PAYMENT ===")
    contractor_id = _prompt_int("contractor_id (TG user id подрядчика)")
    amount_rub = _prompt_int("amount_rub (сумма в рублях)", 1000)
    order_id = _prompt("order_id", "TEST-001")

    r = client.post(
        f"{base}/ui/send/payment",
        data={"contractor_id": contractor_id, "amount_rub": amount_rub, "order_id": order_id},
        timeout=60,
        follow_redirects=True,
    )
    print(f"HTTP {r.status_code}\n{_extract_flash(r.text)}")


def action_pin_order_details(client: httpx.Client, base: str) -> None:
    print("\n=== UI: PIN ORDER DETAILS ===")
    chat_id = _prompt_int("chat_id (ID группы вида -100...)")
    order_id = _prompt("order_id", "TEST-001")
    title = _prompt("title", "TEST-ORDER")

    r = client.post(
        f"{base}/ui/chat/pin-order-details",
        data={"chat_id": chat_id, "order_id": order_id, "title": title},
        timeout=60,
        follow_redirects=True,
    )
    print(f"HTTP {r.status_code}\n{_extract_flash(r.text)}")


def action_send_raw(client: httpx.Client, base: str) -> None:
    print("\n=== UI: SEND RAW ===")
    contractor_id = _prompt_int("contractor_id (TG user id подрядчика)")
    text = _prompt("text", "Тестовое сообщение")
    order_id = _prompt("order_id (пусто = без кнопки)", "")

    r = client.post(
        f"{base}/ui/send/raw",
        data={"contractor_id": contractor_id, "text": text, "order_id": order_id},
        timeout=60,
        follow_redirects=True,
    )
    print(f"HTTP {r.status_code}\n{_extract_flash(r.text)}")


def menu() -> str:
    print("\nВыбери действие:")
    print("  1) open_ui")
    print("  2) health")
    print("  3) send_new_order")
    print("  4) send_payment")
    print("  5) pin_order_details")
    print("  6) send_raw")
    print("  0) exit")
    while True:
        s = input("> ").strip()
        if s in {"1", "2", "3", "4", "5", "6", "0"}:
            return s


def main() -> None:
    ap = argparse.ArgumentParser(description="Console tester for Bot3 Web UI")
    ap.add_argument("--base-url", default="http://127.0.0.1:8002", help="Bot3 base url")
    ap.add_argument(
        "--action",
        choices=["menu", "open_ui", "health", "send_new_order", "send_payment", "pin_order_details", "send_raw"],
        default="menu",
    )
    args = ap.parse_args()

    base = args.base_url.rstrip("/")

    if args.action == "open_ui":
        action_open_ui(base)
        return

    with httpx.Client() as client:
        if args.action == "health":
            action_health(client, base)
            return
        if args.action == "send_new_order":
            action_notify_new_order(client, base)
            return
        if args.action == "send_payment":
            action_notify_payment(client, base)
            return
        if args.action == "pin_order_details":
            action_pin_order_details(client, base)
            return
        if args.action == "send_raw":
            action_send_raw(client, base)
            return

        while True:
            choice = menu()
            if choice == "0":
                print("bye")
                return
            if choice == "1":
                action_open_ui(base)
            elif choice == "2":
                action_health(client, base)
            elif choice == "3":
                action_notify_new_order(client, base)
            elif choice == "4":
                action_notify_payment(client, base)
            elif choice == "5":
                action_pin_order_details(client, base)
            elif choice == "6":
                action_send_raw(client, base)


if __name__ == "__main__":
    main()
