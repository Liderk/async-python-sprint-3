import subprocess
import time

import pytest


@pytest.fixture
def server_process():
    process = subprocess.Popen(['python3', 'server.py'])
    # даем время запустится процессу с сервером
    time.sleep(2)
    yield process
    process.terminate()
