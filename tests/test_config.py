from app.core import config


def test_data_dirs_created_on_import():
    assert config.DATA_DIR.is_dir()
    assert config.MEDIA_DIR.is_dir()
    assert config.MAPS_DIR.is_dir()
    assert config.TOKENS_DIR.is_dir()
    assert config.PORTRAITS_DIR.is_dir()


def test_db_url_targets_data_dir():
    assert config.DB_URL.startswith("sqlite:///")
    assert config.DB_URL.endswith("hexforge.db")


def test_enabled_modules_is_empty_list():
    assert config.ENABLED_MODULES == []


def test_host_and_port_defaults():
    assert isinstance(config.HOST, str)
    assert isinstance(config.PORT, int)
