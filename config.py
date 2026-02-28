import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class TelegramSettings:
    api_id: int
    api_hash: str
    session_name: str
    channels: list


@dataclass
class BaleSettings:
    target_chat_url: str
    browser_data_dir: str
    headless: bool = False
    slow_mo: int = 100


@dataclass
class Settings:
    telegram: TelegramSettings
    bale: BaleSettings
    dedup_db_path: str = "data/seen_configs.db"
    dedup_max_age_hours: int = 168
    log_level: str = "INFO"
    log_file: str = "data/agent.log"


def load_settings(path: str = "config.yaml") -> Settings:
    project_root = Path(__file__).parent
    config_path = project_root / path

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Copy config.yaml.example to config.yaml and fill in your credentials."
        )

    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    tg = raw.get("telegram", {})
    bale = raw.get("bale", {})
    dedup = raw.get("dedup", {})
    log = raw.get("logging", {})

    def resolve(p: str) -> str:
        return str(project_root / p)

    return Settings(
        telegram=TelegramSettings(
            api_id=int(tg["api_id"]),
            api_hash=str(tg["api_hash"]),
            session_name=resolve(tg.get("session_name", "data/session")),
            channels=tg.get("channels", []),
        ),
        bale=BaleSettings(
            target_chat_url=bale.get("target_chat_url", "https://web.bale.ai/chat"),
            browser_data_dir=resolve(bale.get("browser_data_dir", "data/bale_browser")),
            headless=bale.get("headless", False),
            slow_mo=bale.get("slow_mo", 100),
        ),
        dedup_db_path=resolve(dedup.get("db_path", "data/seen_configs.db")),
        dedup_max_age_hours=dedup.get("max_age_hours", 168),
        log_level=log.get("level", "INFO"),
        log_file=resolve(log.get("file", "data/agent.log")),
    )
