import pytest


@pytest.fixture(autouse=True)
def isolated_traces(tmp_path, monkeypatch):
    monkeypatch.setenv('BANJANG_TRACE_DIR', str(tmp_path / 'traces'))
