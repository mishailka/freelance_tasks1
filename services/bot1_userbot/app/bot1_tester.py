#!/usr/bin/env python3
import argparse
import base64
import json
import sys
from typing import Any, Dict, List, Optional

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


def _prompt_int_list(text: str, default: Optional[List[int]] = None) -> List[int]:
    d = ",".join(map(str, default)) if default else ""
    while True:
        s = _prompt(text + " (через запятую)", d if d else None).replace(" ", "")
        if not s:
            return []
        try:
            return [int(x) for x in s.split(",") if x]
        except ValueError:
            print("Введите список целых чисел, например: 111,222,333")


def _read_icon_base64(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    return base64.b64encode(raw).decode("utf-8")


def _pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def req(client: httpx.Client, method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    r = client.request(method, url, json=payload, timeout=60)
    ct = r.headers.get("content-type", "")
    if "application/json" in ct:
        return r.status_code, r.json()
    return r.status_code, r.text


def action_health(client: httpx.Client, base: str) -> None:
    code, body = req(client, "GET", f"{base}/health")
    print(f"HTTP {code}\n{_pretty(body)}")


def action_create_group(client: httpx.Client, base: str) -> None:
    print("\n=== CREATE GROUP ===")
    order_id = _prompt("order_id", "TEST-001")
    title = _prompt("title", f"Заказ {order_id}")
    description = _prompt("description (можно пусто)", "")
    curator_id = _prompt_int("curator_id (числовой TG user id)")
    curator_label = _prompt("curator_label", "Куратор")
    contractor_ids = _prompt_int_list("contractor_ids (TG user id подрядчиков)", [])
    bot2_username = _prompt("bot2_username (без @, можно пусто)", "")
    bot3_username = _prompt("bot3_username (без @, можно пусто)", "")

    icon_path = _prompt("path к иконке (jpg/png, можно пусто)", "")
    icon_base64 = None
    if icon_path:
        try:
            icon_base64 = _read_icon_base64(icon_path)
        except Exception as e:
            print(f"Не смог прочитать иконку: {e}")
            icon_base64 = None

    payload = {
        "order_id": order_id,
        "title": title,
        "description": description if description else None,
        "icon_base64": icon_base64,
        "curator_id": curator_id,
        "curator_label": curator_label,
        "contractor_ids": contractor_ids,
        "bot2_username": bot2_username if bot2_username else None,
        "bot3_username": bot3_username if bot3_username else None,
    }

    code, body = req(client, "POST", f"{base}/api/crm/create_group", payload)
    print(f"HTTP {code}\n{_pretty(body)}")

    # Подсказка для дальнейших шагов
    if isinstance(body, dict) and body.get("ok") and body.get("group_id"):
        print("\nСкопируй group_id для следующих тестов:")
        print("group_id =", body.get("group_id"))
        if body.get("group_link"):
            print("group_link =", body.get("group_link"))


def action_send_fallback(client: httpx.Client, base: str) -> None:
    print("\n=== SEND FALLBACK MESSAGE ===")
    contractor_id = _prompt_int("contractor_id (TG user id подрядчика)")
    group_id = _prompt_int("group_id (ID группы вида -100...)")
    text = _prompt("text", "Фолбэк тест: зайди в чат — потом это сообщение должно удалиться.")

    payload = {"contractor_id": contractor_id, "group_id": group_id, "text": text}
    code, body = req(client, "POST", f"{base}/api/crm/send_fallback_message", payload)
    print(f"HTTP {code}\n{_pretty(body)}")


def action_remove_contractor(client: httpx.Client, base: str) -> None:
    print("\n=== REMOVE CONTRACTOR ===")
    chat_id = _prompt_int("chat_id (ID группы вида -100...)")
    contractor_id = _prompt_int("contractor_id (TG user id подрядчика)")

    payload = {"chat_id": chat_id, "contractor_id": contractor_id}
    code, body = req(client, "POST", f"{base}/api/crm/remove_contractor", payload)
    print(f"HTTP {code}\n{_pretty(body)}")


def interactive_menu() -> str:
    print("\nВыбери действие:")
    print("  1) health")
    print("  2) create_group")
    print("  3) send_fallback_message")
    print("  4) remove_contractor")
    print("  0) exit")
    while True:
        s = input("> ").strip()
        if s in {"1", "2", "3", "4", "0"}:
            return s


def main():
    ap = argparse.ArgumentParser(description="Console tester for Bot1 Userbot API")
    ap.add_argument("--base-url", default="http://127.0.0.1:8001", help="Bot1 base url, e.g. http://localhost:8001")
    ap.add_argument("--action", choices=["health", "create_group", "send_fallback_message", "remove_contractor", "menu"],
                    default="menu")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")

    with httpx.Client() as client:
        if args.action == "health":
            action_health(client, base)
            return
        if args.action == "create_group":
            action_create_group(client, base)
            return
        if args.action == "send_fallback_message":
            action_send_fallback(client, base)
            return
        if args.action == "remove_contractor":
            action_remove_contractor(client, base)
            return

        # menu mode
        while True:
            choice = interactive_menu()
            if choice == "0":
                print("bye")
                return
            if choice == "1":
                action_health(client, base)
            elif choice == "2":
                action_create_group(client, base)
            elif choice == "3":
                action_send_fallback(client, base)
            elif choice == "4":
                action_remove_contractor(client, base)


if __name__ == "__main__":
    main()
