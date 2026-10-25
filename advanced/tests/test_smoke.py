from fastapi.testclient import TestClient
from seatlab.app import create_app

def test_health(tmp_path):
    with TestClient(create_app(str(tmp_path/'smoke.db'))) as client:
        assert client.get('/health').status_code==200
