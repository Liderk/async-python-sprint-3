import pytest

from client import Client


@pytest.fixture
def client_1():
    client = Client(port=50007)
    return client


@pytest.fixture
def client_2():
    client = Client(port=50007)
    return client