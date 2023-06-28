import asyncio
from asyncio import StreamReader, StreamWriter
import logging
from typing import Tuple, Dict, List

from users import User

logger = logging.getLogger(__file__)


class ChatConnectionError(Exception):
    pass


class ClientDisconnect(Exception):
    pass


class Server:
    def __init__(self, host: str = "127.0.0.1", port: int = 50007,
                 backlog: int = 100, history_size: int = 20):
        self.host: str = host
        self.port: int = port
        self.backlog: int = backlog
        self.history_size: int = history_size
        self.clients: Dict[str, User] = {}
        self._client_peer_mapping: Dict[Tuple, str] = {}
        self.history: List = []

    def _add_client(self, writer: StreamWriter, username: str):
        _, peer_name = self.__get_user_data(writer)

        if username in self.clients:
            user: User = self.clients.get(username)
        else:
            user = User(username, [])

        user.writers.append(writer)
        self.clients[username] = user
        self._client_peer_mapping[peer_name] = username

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        writer.write(b"Welcome to the server!\n")
        while True:
            data = await reader.readline()
            if not data:
                break
            msg = data.decode().strip()
            logger.info(msg)

            try:
                await self.dispatch(msg, writer)
            except (ValueError, ChatConnectionError) as err:
                logger.error(err, exc_info=True)
                writer.write(f"{err}\n".encode())
            except ClientDisconnect:
                break

        await self._quit(writer)

    async def dispatch(self, msg: str, writer: StreamWriter):
        handler_name, message = self.__get_message_data(msg)
        logger.debug("handler name %s", handler_name)
        _, peer = self.__get_user_data(writer)

        if handler_name != "connect" and peer not in self._client_peer_mapping:
            msg = 'To start chat, you must run "/connect"'
            raise ChatConnectionError(msg)

        handler = getattr(self, handler_name, None)

        if handler:
            logger.debug("Get handler")
            if message:
                await handler(message, writer)
            else:
                await handler(writer)
        else:
            raise ValueError(
                "No handler for message type %s" % handler_name)

    @staticmethod
    def __get_message_data(incoming_data: str) -> Tuple:
        if incoming_data.startswith("/send"):
            if "->" in incoming_data:
                action = "private"
                _, message = incoming_data.split("->", 1)
            else:
                action = "broadcast"
                _, message = incoming_data.split(" ", 1)

        elif incoming_data.startswith("/status"):
            message = None
            action = "status"

        elif incoming_data.startswith("/connect"):
            _, message = incoming_data.split(" ", 1)
            action = "connect"

        elif incoming_data.startswith("/quit"):
            message = None
            action = "quit"
        else:
            message = None
            action = None

        return action, message

    async def connect(self, username: str, writer: StreamWriter):
        self._add_client(writer, username)
        writer.write(b"You are now connected!\n")
        await self.send_history(writer)

    async def status(self, writer: StreamWriter):
        writer.write(f"Connected clients: {len(self.clients)}\n".encode())
        writer.write(f"History size: {len(self.history)}\n".encode())

    async def private(self, message: str, sender: StreamWriter):
        logger.info("now private")

        sender_username, sender_peer = self.__get_user_data(sender)

        recipient, message = message.split("->", 1)
        recipient = recipient.strip()
        message = message.strip()

        if recipient not in self.clients:
            sender.write(f"Error: recipient not found\n".encode())
        else:
            for user in self.clients.values():
                if user.username != recipient:
                    continue
                for user_writer in user.writers:
                    if user_writer == sender:
                        continue
                    msg = f"(private) {sender_username}: {message}\n".encode()
                    user_writer.write(msg)

    async def broadcast(self, message: str, sender: StreamWriter):
        sender_username, sender_peer = self.__get_user_data(sender)
        if not sender_username:
            sender_username = "admin"

        self.history.append(f"{sender_username}: {message}")

        if len(self.history) > self.history_size:
            self.history.pop(0)

        for username, user in self.clients.items():
            for user_write in user.writers:
                if user_write.get_extra_info("peername") == sender_peer:
                    continue
                user_write.write(f"{sender_username}: {message}\n".encode())

    async def send_history(self, writer: StreamWriter):
        for message in self.history[-self.history_size:]:
            writer.write(f"{message}\n".encode())
            await writer.drain()

    async def run(self):
        server_chat = await asyncio.start_server(self.handle_client, self.host,
                                                 self.port,
                                                 backlog=self.backlog)
        logger.info("Start server")
        async with server_chat:
            await server_chat.serve_forever()

    def __get_user_data(self,
                        writer: StreamWriter) -> Tuple[str, Tuple]:
        peer = writer.get_extra_info("peername")
        username = self._client_peer_mapping.get(peer)
        return username, peer

    async def quit(self, writer: StreamWriter):
        raise ClientDisconnect

    async def _quit(self, writer: StreamWriter):
        username, peer = self.__get_user_data(writer)
        if username:
            self.clients.pop(username)
            self._client_peer_mapping.pop(peer)
        message = f"{username} leaving us!"
        await self.broadcast(message, writer)
        writer.write("/quit\n".encode())
        writer.close()


if __name__ == "__main__":
    server = Server(
        host="127.0.0.1",
        port=50007,
    )
    asyncio.run(server.run())
