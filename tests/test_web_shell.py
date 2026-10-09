"""모바일 웹 프로젝트의 설정을 확인한다."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def test_web_project_config():
    """지정한 명령으로 실행할 수 있는 웹 프로젝트여야 한다."""
    package = json.loads((WEB / "package.json").read_text())
    assert package["name"] == "banjang-web"
    assert package["private"] is True
    assert package["scripts"] == {
        "dev": "vite", "build": "vite build", "preview": "vite preview"
    }
    html = (WEB / "index.html").read_text()
    assert 'lang="ko"' in html
    assert "viewport-fit=cover" in html
    assert '<title>안전반장</title>' in html
