import os
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_upgrade_creates_and_seeds_campaign(tmp_path: Path):
    db_file = tmp_path / "t.db"
    os.environ["HEXFORGE_DB_URL"] = f"sqlite:///{db_file.as_posix()}"
    try:
        cfg = Config(str(Path("alembic.ini").resolve()))
        command.upgrade(cfg, "head")

        import sqlite3

        con = sqlite3.connect(db_file)
        rows = con.execute("select name, active from campaign").fetchall()
        con.close()
        assert ("My Campaign", 1) in rows
    finally:
        del os.environ["HEXFORGE_DB_URL"]
