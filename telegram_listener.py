import asyncio
import logging

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

from config_detector import extract_configs

logger = logging.getLogger(__name__)


class TelegramListener:
    def __init__(self, settings, on_configs_found):
        """
        settings: TelegramSettings dataclass
        on_configs_found: async callback(configs: list[dict])
        """
        self.settings = settings
        self.on_configs_found = on_configs_found
        self.client = TelegramClient(
            settings.session_name,
            settings.api_id,
            settings.api_hash,
        )
        self._channel_entities = []

    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            logger.error(
                "Telegram session not authorized. "
                "Run 'python auth_telegram.py' in your terminal first."
            )
            raise RuntimeError("Telegram not authenticated. Run: python auth_telegram.py")
        me = await self.client.get_me()
        logger.info("Telegram client started as %s", me.username or me.phone)

        for ch in self.settings.channels:
            try:
                entity = await self.client.get_entity(ch)
                self._channel_entities.append(entity)
                title = getattr(entity, "title", str(ch))
                logger.info("Monitoring channel: %s (id=%d)", title, entity.id)
            except FloodWaitError as e:
                logger.warning("Flood wait for %d seconds resolving %s, waiting...", e.seconds, ch)
                await asyncio.sleep(e.seconds)
                entity = await self.client.get_entity(ch)
                self._channel_entities.append(entity)
            except Exception as e:
                logger.error("Could not resolve channel %s: %s", ch, e)

        if not self._channel_entities:
            logger.error("No channels resolved. Nothing to monitor.")
            return

        # Register handler for new messages only (no old messages)
        channel_ids = [e.id for e in self._channel_entities]

        @self.client.on(events.NewMessage(chats=channel_ids))
        async def handler(event):
            text = event.message.message
            if not text:
                return
            configs = extract_configs(text)
            if configs:
                logger.info(
                    "Found %d config(s) in channel %s",
                    len(configs),
                    event.chat_id,
                )
                await self.on_configs_found(configs)

    async def run_forever(self):
        await self.start()
        logger.info("Listening for new messages...")
        await self.client.run_until_disconnected()

    async def stop(self):
        await self.client.disconnect()
