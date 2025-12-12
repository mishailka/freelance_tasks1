from __future__ import annotations

import base64
import io
import logging
import tempfile
from dataclasses import dataclass
from typing import Optional, List

from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.raw import functions
from pyrogram.types import Chat

from .config import settings
from .storage import Storage

log = logging.getLogger("bot1.telegram")


@dataclass
class GroupResult:
    ok: bool
    group_id: Optional[int] = None
    group_link: Optional[str] = None
    error: Optional[str] = None


class TelegramUserbot:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.client = Client(
            name="bot1_userbot",
            api_id=settings.tg_api_id,
            api_hash=settings.tg_api_hash,
            session_string=settings.pyrogram_session_string,
            workdir="/data",
            in_memory=False,
        )

        # event handlers
        @self.client.on_chat_member_updated()
        async def _on_member_update(_, update):
            # If a contractor joined the group, delete previously sent fallback message in private chat
            try:
                group_id = update.chat.id
                user_id = update.new_chat_member.user.id if update.new_chat_member else None
                if not user_id:
                    return
                row = self.storage.get_fallback_message(contractor_id=user_id, group_id=group_id)
                if not row:
                    return
                # delete outgoing message in user's private chat
                try:
                    await self.client.delete_messages(chat_id=user_id, message_ids=[row.message_id])
                finally:
                    self.storage.delete_fallback_message(row.id)
                    log.info("Deleted fallback message %s for user %s in group %s", row.message_id, user_id, group_id)
            except Exception:
                log.exception("Failed handling chat_member_updated")

    async def start(self) -> None:
        await self.client.start()
        me = await self.client.get_me()
        log.info("Bot1 userbot started as %s", me.id)

    async def stop(self) -> None:
        await self.client.stop()

    async def _set_chat_photo(self, chat_id: int, icon_base64: str) -> None:
        raw = base64.b64decode(icon_base64)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as f:
            f.write(raw)
            f.flush()
            await self.client.set_chat_photo(chat_id, photo=f.name)

    async def _open_history_for_users(self, chat_id: int) -> None:
        # Best effort: Telegram setting "Chat history for new members"
        # Using raw ToggleChatPreHistoryHidden(enabled=False) (name can differ by layer)
        try:
            peer = await self.client.resolve_peer(chat_id)
            await self.client.invoke(functions.messages.ToggleChatPreHistoryHidden(peer=peer, enabled=False))
            log.info("Opened history for users in chat %s", chat_id)
        except Exception as e:
            log.warning("Could not toggle pre-history visibility in chat %s: %s", chat_id, e)

    async def _delete_recent_messages(self, chat_id: int, limit: int = 50) -> None:
        ids = []
        async for m in self.client.get_chat_history(chat_id, limit=limit):
            ids.append(m.id)
        if ids:
            try:
                await self.client.delete_messages(chat_id, message_ids=ids, revoke=True)
            except Exception as e:
                log.warning("Failed deleting recent messages in chat %s: %s", chat_id, e)

    async def create_and_setup_group(
        self,
        title: str,
        description: Optional[str],
        icon_base64: Optional[str],
        curator_id: int,
        curator_label: str,
        contractor_ids: List[int],
        bot2_username: str,
        bot3_username: str,
    ) -> GroupResult:
        try:
            # Create group with curator as initial member (Telegram requires at least one invite)
            chat: Chat = await self.client.create_group(title=title, users=[curator_id])
            chat_id = chat.id

            if description:
                try:
                    await self.client.set_chat_description(chat_id, description)
                except Exception as e:
                    log.warning("Failed setting description: %s", e)

            if icon_base64:
                try:
                    await self._set_chat_photo(chat_id, icon_base64)
                except Exception as e:
                    log.warning("Failed setting photo: %s", e)

            # Add bots and promote them
            # Telegram expects usernames without @
            for uname in [bot2_username, bot3_username]:
                try:
                    await self.client.add_chat_members(chat_id, [uname])
                except RPCError as e:
                    log.warning("Failed adding %s: %s", uname, e)

                try:
                    await self.client.promote_chat_member(
                        chat_id,
                        uname,
                        can_manage_chat=True,
                        can_delete_messages=True,
                        can_manage_video_chats=True,
                        can_restrict_members=True,
                        can_promote_members=False,
                        can_change_info=True,
                        can_invite_users=True,
                        can_pin_messages=True,
                        is_anonymous=True,
                    )
                except Exception as e:
                    log.warning("Failed promoting %s as anonymous admin: %s", uname, e)

            # Promote curator + set label (custom title)
            try:
                await self.client.promote_chat_member(
                    chat_id,
                    curator_id,
                    can_manage_chat=True,
                    can_delete_messages=True,
                    can_manage_video_chats=True,
                    can_restrict_members=True,
                    can_promote_members=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                )
                await self.client.set_administrator_title(chat_id, curator_id, curator_label)
            except Exception as e:
                log.warning("Failed promoting curator: %s", e)

            # Add contractors
            if contractor_ids:
                try:
                    await self.client.add_chat_members(chat_id, contractor_ids)
                except Exception as e:
                    log.warning("Failed adding contractors: %s", e)

            # Delete service messages / clear chat
            await self._delete_recent_messages(chat_id)

            # Open history
            await self._open_history_for_users(chat_id)

            # Export invite link
            group_link = None
            try:
                group_link = await self.client.export_chat_invite_link(chat_id)
            except Exception as e:
                log.warning("Failed exporting invite link: %s", e)

            return GroupResult(ok=True, group_id=chat_id, group_link=group_link)
        except Exception as e:
            log.exception("create_and_setup_group failed")
            return GroupResult(ok=False, error=str(e))

    async def remove_contractor(self, chat_id: int, contractor_id: int) -> None:
        # Kick via ban+unban
        try:
            await self.client.ban_chat_member(chat_id, contractor_id)
            await self.client.unban_chat_member(chat_id, contractor_id)
        except Exception as e:
            log.warning("Failed removing contractor %s from %s: %s", contractor_id, chat_id, e)
            raise

    async def send_fallback_message_and_track(self, contractor_id: int, group_id: int, text: str) -> int:
        msg = await self.client.send_message(contractor_id, text)
        self.storage.add_fallback_message(contractor_id=contractor_id, group_id=group_id, message_id=msg.id)
        return msg.id
