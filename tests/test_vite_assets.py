from __future__ import annotations

import json

import pytest

from app.core import config, vite_assets


def test_dev_mode_emits_client_and_entry(monkeypatch):
    monkeypatch.setattr(config, "VITE_DEV", True)
    monkeypatch.setattr(config, "VITE_DEV_SERVER_URL", "http://localhost:5173")
    html = str(vite_assets.vite_entry())
    assert "http://localhost:5173/@vite/client" in html
    assert f"http://localhost:5173/{config.VITE_ENTRY}" in html
    assert 'type="module"' in html


def test_prod_mode_emits_hashed_asset_from_manifest(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    (dist / ".vite").mkdir(parents=True)
    manifest = {
        config.VITE_ENTRY: {
            "file": "assets/main-abc123.js",
            "css": ["assets/main-abc123.css"],
        }
    }
    (dist / ".vite" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setattr(config, "VITE_DEV", False)
    monkeypatch.setattr(config, "VITE_DIST_DIR", dist)
    html = str(vite_assets.vite_entry())
    assert '<script type="module" src="/static/dist/assets/main-abc123.js">' in html
    assert '<link rel="stylesheet" href="/static/dist/assets/main-abc123.css">' in html


def test_prod_mode_degrades_when_manifest_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "VITE_DEV", False)
    monkeypatch.setattr(config, "VITE_DIST_DIR", tmp_path / "nonexistent")
    html = str(vite_assets.vite_entry())
    assert "<script" not in html  # no broken asset tags
    assert "not built" in html.lower()  # a hint comment, not an exception


def test_prod_mode_raises_when_entry_missing_from_manifest(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    (dist / ".vite").mkdir(parents=True)
    (dist / ".vite" / "manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config, "VITE_DEV", False)
    monkeypatch.setattr(config, "VITE_DIST_DIR", dist)
    with pytest.raises(KeyError):
        vite_assets.vite_entry()
