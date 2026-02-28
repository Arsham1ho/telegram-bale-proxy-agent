import asyncio
import logging
import signal
import sys
from pathlib import Path

from config import load_settings
from telegram_listener import TelegramListener
from bale_sender import BaleSender
from dedup import DedupStore


async def main():
    settings = load_settings()

    # Ensure data directory exists
    Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger("main")

    # Initialize components
    dedup = DedupStore(settings.dedup_db_path, settings.dedup_max_age_hours)
    dedup.purge_old()
    logger.info("Dedup store initialized")

    bale = BaleSender(settings.bale)
    await bale.start()
    logger.info("Bale sender ready")

    async def on_configs_found(configs: list[dict]):
        for cfg in configs:
            if dedup.is_seen(cfg["hash"]):
                logger.debug("Skipping duplicate: %s... (%s)", cfg["raw"][:40], cfg["type"])
                continue
            logger.info("Forwarding %s config: %s...", cfg["type"], cfg["raw"][:60])
            EMOJI_MAP = {
                "vmess": "\u26a1",
                "vless": "\U0001f680",
                "ss": "\U0001f30d",
                "trojan": "\U0001f40e",
                "reality": "\U0001f510",
                "hy2": "\U0001f4a8",
                "hysteria2": "\U0001f4a8",
                "hysteria": "\U0001f4a8",
                "wireguard": "\U0001f6e1\ufe0f",
                "tg_proxy": "\U0001f4e1",
                "json_v2ray": "\U0001f4cb",
            }
            emoji = EMOJI_MAP.get(cfg["type"], "\u2705")
            message = f"{cfg['raw']} {emoji}"
            success = await bale.send_config(message)
            if success:
                dedup.mark_seen(cfg["hash"], cfg["type"], cfg["raw"][:100])
                logger.info("Forwarded %s config (hash=%s...)", cfg["type"], cfg["hash"][:12])
            else:
                logger.error("Failed to forward config, will retry next time")

    listener = TelegramListener(settings.telegram, on_configs_found)

    # Graceful shutdown
    shutdown_event = asyncio.Event()

    def handle_signal():
        logger.info("Shutdown signal received")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    logger.info("Starting agent. Monitoring %d channels.", len(settings.telegram.channels))
    await listener.start()

    # Run until shutdown signal
    disconnect_task = asyncio.create_task(listener.client.run_until_disconnected())
    shutdown_task = asyncio.create_task(shutdown_event.wait())

    done, pending = await asyncio.wait(
        [disconnect_task, shutdown_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

    # Cleanup
    logger.info("Shutting down...")
    await listener.stop()
    await bale.stop()
    dedup.close()
    logger.info("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
