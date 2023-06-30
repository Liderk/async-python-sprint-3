import asyncio
import logging
from typing import Optional

from logger_config import get_logger
from settings import settings

logger = logging.getLogger(__file__)


class Client:
    def __init__(self, host="127.0.0.1", port=50007):
        self.host: str = host
        self.port: int = port
        self.reader = None
        self.writer = None
        self.client_connect: bool = False
        self.username: Optional[str] = None

    async def connect(self):
        self.username = input("Enter your username: ")
        self.reader, self.writer = await asyncio.open_connection(self.host,
                                                                 self.port)
        self.client_connect = True

    async def _send(self, message):
        self.writer.write(message.encode() + b"\n")
        logger.debug("Сообщение отправлено")
        await self.writer.drain()

    async def send_to_server(self):
        logger.debug("Ожидаю ввод команды")
        loop = asyncio.get_event_loop()
        while self.client_connect:
            try:
                message = await loop.run_in_executor(None, input)
            except KeyboardInterrupt:
                message = "/quit"

            logger.debug(f"Введено: {message}")
            if message.startswith("/private"):
                message = message.replace("/private ", "")
                recipient, message = message.split(" ", 1)
                await self._send(f"/send {recipient} -> {message}")
            elif message.startswith("/connect"):
                await self._send(f"/connect {self.username}")
            elif message.startswith("/quit"):
                await self._send(f"{message}")
                self.client_connect = False
            elif message.startswith("/status"):
                await self._send(f"{message}")
            else:
                await self._send(f"/send {message}")
            await asyncio.sleep(0.1)

    async def _receive(self):
        logger.debug("Начинаю читать редер")
        data = await self.reader.readline()
        logger.debug("редер прочитан")
        return data.decode().strip()

    async def receive_messages(self):
        while self.client_connect:
            logger.debug("Начинаю принимать сообщения")
            try:
                message = await self._receive()
            except KeyboardInterrupt:
                message = "/quit"
            if message == "/quit":
                logger.debug("Exit")
                self.client_connect = False
            print(message)

    async def run(self):
        logger.debug("Connecting start")
        await self.connect()
        logger.debug("start gather")
        await asyncio.gather(self.receive_messages(), self.send_to_server())


if __name__ == "__main__":
    logger = get_logger(__file__)
    client = Client(
        host=settings.host,
        port=settings.port,
    )
    asyncio.run(client.run())
