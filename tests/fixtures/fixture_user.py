import pytest

from users import User


@pytest.fixture
def users():
    first = User("test1", [])
    second = User("test2", [])
    return first, second
