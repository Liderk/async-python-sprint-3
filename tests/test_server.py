from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_connect(client_1, users, server_process):
    user, _ = users
    with patch("builtins.input", return_value=user.username):
        await client_1.connect()

    assert client_1.client_connect, "Должно быть подключение к серверу"
    assert client_1.username == user.username, "Должно быть установленно имя"
    assert client_1.reader is not None, "reader is not None"
    assert client_1.writer is not None, "writer is not None"

    res = await client_1._receive()
    assert res == "Welcome to the server!"

    await client_1._send(f"/connect {user.username}")
    res = await client_1._receive()
    msg = "Сервер должен прислать ответ успешного подключения"
    assert res == "You are now connected!", msg

    await client_1._send("/status")
    res = await client_1._receive()
    msg = "Количество подключенных клиентов должно быть 1"
    assert res == "Connected clients: 1", msg
    res = await client_1._receive()
    msg = "Количество сообщение должно быть равно 0"
    assert res == "History size: 0", msg

    await client_1._send("/send test_question 1")
    await client_1._send("/send test_question 2")

    await client_1._send("/status")
    res = await client_1._receive()
    msg = "Количество подключенных клиентов должно быть 1"
    assert res == "Connected clients: 1", msg
    res = await client_1._receive()
    msg = "Количество сообщение должно быть равно 2"
    assert res == "History size: 2", msg


@pytest.mark.asyncio
async def test_chat(client_1, client_2, users, server_process):
    user1, user2 = users

    with patch("builtins.input", return_value=user1.username):
        await client_1.connect()

    await client_1._send(f"/connect {user1.username}")
    await client_1._receive()  # Пропускаем приветствие
    await client_1._receive()  # Пропускаем что мы присоединились к серверу

    with patch("builtins.input", return_value=user2.username):
        await client_2.connect()

    await client_2._send(f"/connect {user2.username}")
    await client_2._receive()  # Пропускаем приветствие
    await client_2._receive()  # Пропускаем что мы присоединились к серверу

    await client_1._send("/send hi!")

    res = await client_2._receive()
    msg = "Сообщение отправленное одним юзером, должно прийти другому"
    assert res == "test1: hi!", msg

    await client_2._send(f"/send {user1.username} -> private message")

    res = await client_1._receive()
    assert res == "(private) test2: private message", msg
