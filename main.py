import asyncio

from logger_config import get_logger
from server import Server

if __name__ == "__main__":
    logger = get_logger(__file__)
    server = Server(
        host="127.0.0.1",
        port=50007,
    )
    asyncio.run(server.run())
