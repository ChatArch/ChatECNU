from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_mkdocs_material_icons_render_without_literal_tokens(tmp_path: Path) -> None:
    site_dir = tmp_path / "site"
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(site_dir)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    checked = {
        "zh_home": site_dir / "index.html",
        "en_home": site_dir / "en" / "index.html",
    }
    for name, page in checked.items():
        html = page.read_text(encoding="utf-8")
        assert ":material-" not in html, name
        assert "twemoji" in html or "md-icon" in html, name
