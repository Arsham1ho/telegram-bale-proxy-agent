"""Run this script once in your terminal to authenticate with Telegram.
After successful login, the session is saved and main.py won't ask again.

Usage:
    python auth_telegram.py
"""
import asyncio
from config import load_settings
from telethon import TelegramClient


async def main():
    settings = load_settings()
    client = TelegramClient(
        settings.telegram.session_name,
        settings.telegram.api_id,
        settings.telegram.api_hash,
    )
    print("Starting Telegram authentication...")
    print("You will be asked for your phone number and a verification code.\n")
    await client.start()
    me = await client.get_me()
    print(f"\nSuccess! Logged in as: {me.username or me.phone}")
    print("Session saved. You can now run: python main.py")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
