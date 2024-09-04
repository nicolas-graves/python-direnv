import pytest


@pytest.fixture
def dotenv_path(tmp_path):
    path = tmp_path / '.env'
    path.write_bytes(b'')
    yield path


@pytest.fixture
def direnv_allow(monkeypatch):
    monkeypatch.setattr("direnv.main.is_allowed", lambda _: True)
