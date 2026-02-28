import asyncio
import logging

from playwright.async_api import async_playwright, BrowserContext, Page

logger = logging.getLogger(__name__)


class BaleSender:
    def __init__(self, settings):
        self.settings = settings
        self.playwright = None
        self.context: BrowserContext = None
        self.page: Page = None
        self._lock = asyncio.Lock()

    async def start(self):
        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.settings.browser_data_dir,
            headless=self.settings.headless,
            slow_mo=self.settings.slow_mo,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        await self._navigate_to_chat()

    async def _navigate_to_chat(self):
        url = self.settings.target_chat_url
        logger.info("Navigating to %s", url)
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await self.page.wait_for_timeout(8000)

        # Check if login is needed
        login_indicators = ['input[type="tel"]', '[class*="qr-code"]', '[class*="QrCode"]']
        is_login = False
        for sel in login_indicators:
            if await self.page.query_selector(sel):
                is_login = True
                break

        if is_login:
            logger.warning("=" * 50)
            logger.warning("MANUAL LOGIN REQUIRED")
            logger.warning("Please log in to Bale in the browser window.")
            logger.warning("The script will continue automatically after login.")
            logger.warning("=" * 50)
            await self.page.wait_for_selector('#editable-message-text', timeout=300_000)
            logger.info("Login detected. Continuing...")
            await self.page.wait_for_timeout(3000)

        # Verify the chat opened
        has_input = await self.page.query_selector('#editable-message-text')
        if has_input:
            logger.info("Target chat opened successfully.")
        else:
            logger.warning("Message input not found. Waiting 60s for manual intervention...")
            await self.page.screenshot(path="data/debug_chat_not_found.png")
            await self.page.wait_for_timeout(60000)

    async def send_config(self, config_text: str) -> bool:
        """Send a config string to the open Bale chat."""
        async with self._lock:
            try:
                # Find the message input (#editable-message-text)
                input_el = await self.page.query_selector('#editable-message-text')
                if not input_el:
                    # Fallback to any contenteditable
                    input_el = await self.page.query_selector('[contenteditable="true"]')

                if not input_el:
                    logger.error("Could not find message input box")
                    await self.page.screenshot(path="data/debug_no_input.png")
                    return False

                await input_el.click()
                await self.page.keyboard.insert_text(config_text)
                await self.page.wait_for_timeout(500)

                # Click the send button (aria-label="send-button")
                send_btn = await self.page.query_selector('[aria-label="send-button"]')
                if send_btn:
                    # Use JS click to bypass the overlay div
                    await send_btn.evaluate("el => el.click()")
                else:
                    # Fallback: press Enter
                    logger.debug("Send button not found, pressing Enter")
                    await self.page.keyboard.press("Enter")

                await self.page.wait_for_timeout(1000)
                logger.info("Config sent to Bale successfully")
                return True

            except Exception as e:
                logger.error("Failed to send config to Bale: %s", e)
                try:
                    await self.page.screenshot(path="data/debug_send_error.png")
                except Exception:
                    pass
                return False

    async def stop(self):
        try:
            if self.context:
                await self.context.close()
        except Exception:
            pass
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
