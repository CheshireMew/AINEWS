import httpx
import logging

class TelegramBot:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Send a message to the configured telegram chat.
        Returns True if successful, False otherwise.
        """
        if not self.token or not self.chat_id:
            logging.error("Telegram Bot: Token or Chat ID missing.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                if response.status_code == 200:
                    logging.info(f"Telegram Push Success to {self.chat_id}")
                    return True
                else:
                    logging.error(f"Telegram Push Failed: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logging.error(f"Telegram Push Error: {e}")
            return False

    async def test_connection(self) -> dict:
        """
        Test the bot token validation (getMe).
        """
        if not self.token:
            return {"ok": False, "error": "Token missing"}
            
        url = f"{self.base_url}/getMe"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                return response.json()
        except Exception as e:
             return {"ok": False, "error": str(e)}
