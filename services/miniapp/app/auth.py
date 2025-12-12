from __future__ import annotations

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, Request

from .config import settings


def _check_telegram_webapp_signature(init_data: str, bot_token: str) -> Dict:
    # Telegram WebApp initData validation:
    # https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    pairs = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(pairs)

    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Bad initData signature")

    # optional: check auth_date is not too old (48h)
    auth_date = data.get("auth_date")
    if auth_date:
        try:
            ts = int(auth_date)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            age = (datetime.now(tz=timezone.utc) - dt).total_seconds()
            if age > 172800:  # 48h
                raise HTTPException(status_code=401, detail="initData expired")
        except ValueError:
            pass

    user_raw = data.get("user")
    if not user_raw:
        raise HTTPException(status_code=401, detail="Missing user in initData")

    user = json.loads(user_raw)
    return user


async def get_current_contractor_id(
    request: Request,
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    x_debug_user_id: Optional[str] = Header(None, alias="X-Debug-User-Id"),
) -> int:
    if settings.telegram_auth_disabled:
        if not x_debug_user_id:
            raise HTTPException(status_code=401, detail="TELEGRAM_AUTH_DISABLED: provide X-Debug-User-Id")
        return int(x_debug_user_id)

    init_data = x_telegram_init_data or request.query_params.get("initData")
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData (use X-Telegram-Init-Data header)")
    user = _check_telegram_webapp_signature(init_data, settings.bot3_token)
    return int(user["id"])
