"""Generate PYROGRAM_SESSION_STRING for Bot1.

Run:
  pip install pyrogram tgcrypto
  python services/scripts/generate_pyrogram_session.py
"""

from pyrogram import Client
from getpass import getpass

api_id = int(input("TG_API_ID: ").strip())
api_hash = getpass("TG_API_HASH (hidden input): ").strip()

with Client(
    name="session_gen",
    api_id=api_id,
    api_hash=api_hash,
    in_memory=True,
) as app:
    session = app.export_session_string()
    print("\nPYROGRAM_SESSION_STRING=\n" + session + "\n")
