#!/usr/bin/env python3
import argparse
import json
import sys
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:
    print("Не найден модуль httpx. Установи: pip install httpx", file=sys.stderr)
    sys.exit(1)


def _pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


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


def request_json(
    client: httpx.Client,
    method: str,
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
):
    r = client.request(method, url, json=payload, headers=headers, timeout=60)
    ct = r.headers.get("content-type", "")
    if "application/json" in ct:
        return r.status_code, r.json()
    return r.status_code, r.text


def action_health(client: httpx.Client, base: str, headers: Dict[str, str]) -> None:
    code, body = request_json(client, "GET", f"{base}/health", headers=headers or None)
    print(f"HTTP {code}\n{_pretty(body)}")


def action_notify_new_order(client: httpx.Client, base: str, headers: Dict[str, str]) -> None:
    print("\n=== NOTIFY NEW ORDER ===")
    contractor_id = _prompt_int("contractor_id (TG user id подрядчика)")
    order_title = _prompt("order_title", "TEST-ORDER")
    group_link = _prompt("group_link (инвайт-ссылка на чат)", "https://t.me/...")
    group_id = _prompt_int("group_id (ID группы вида -100..., нужен для fallback)", -1001234567890)

    payload = {
        "contractor_id": contractor_id,
        "order_title": order_title,
        "group_link": group_link,
        "group_id": group_id,
    }

    code, body = request_json(client, "POST", f"{base}/api/crm/notify_new_order", payload, headers=headers or None)
    print(f"HTTP {code}\n{_pretty(body)}")


def action_notify_payment(client: httpx.Client, base: str, headers: Dict[str, str]) -> None:
    print("\n=== NOTIFY PAYMENT ===")
    contractor_id = _prompt_int("contractor_id (TG user id подрядчика)")
    amount_rub = _prompt_int("amount_rub (сумма в рублях)", 1000)
    order_id = _prompt("order_id", "TEST-001")

    payload = {
        "contractor_id": contractor_id,
        "amount_rub": amount_rub,
        "order_id": order_id,
    }

    code, body = request_json(client, "POST", f"{base}/api/crm/notify_payment", payload, headers=headers or None)
    print(f"HTTP {code}\n{_pretty(body)}")


def action_pin_order_details(client: httpx.Client, base: str, headers: Dict[str, str]) -> None:
    print("\n=== PIN ORDER DETAILS ===")
    chat_id = _prompt_int("chat_id (ID группы вида -100...)")
    order_id = _prompt("order_id", "TEST-001")
    title = _prompt("title", "TEST-ORDER")

    payload = {
        "chat_id": chat_id,
        "order_id": order_id,
        "title": title,
    }

    code, body = request_json(client, "POST", f"{base}/api/crm/pin_order_details", payload, headers=headers or None)
    print(f"HTTP {code}\n{_pretty(body)}")


def menu() -> str:
    print("\nВыбери действие:")
    print("  1) health")
    print("  2) notify_new_order")
    print("  3) notify_payment")
    print("  4) pin_order_details")
    print("  0) exit")
    while True:
        s = input("> ").strip()
        if s in {"1", "2", "3", "4", "0"}:
            return s


def main():
    ap = argparse.ArgumentParser(description="Console tester for Bot3 Notify Bot API")
    ap.add_argument("--base-url", default="http://127.0.0.1:8002", help="Bot3 base url, e.g. http://localhost:8002")
    ap.add_argument("--api-key", default="", help="Optional X-CRM-API-Key if Bot3 still requires it")
    ap.add_argument(
        "--action",
        choices=["menu", "health", "notify_new_order", "notify_payment", "pin_order_details"],
        default="menu",
    )
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    headers = {}
    if args.api_key.strip():
        headers["X-CRM-API-Key"] = args.api_key.strip()

    with httpx.Client() as client:
        if args.action == "health":
            action_health(client, base, headers)
            return
        if args.action == "notify_new_order":
            action_notify_new_order(client, base, headers)
            return
        if args.action == "notify_payment":
            action_notify_payment(client, base, headers)
            return
        if args.action == "pin_order_details":
            action_pin_order_details(client, base, headers)
            return

        # menu loop
        while True:
            choice = menu()
            if choice == "0":
                print("bye")
                return
            if choice == "1":
                action_health(client, base, headers)
            elif choice == "2":
                action_notify_new_order(client, base, headers)
            elif choice == "3":
                action_notify_payment(client, base, headers)
            elif choice == "4":
                action_pin_order_details(client, base, headers)


if __name__ == "__main__":
    main()
