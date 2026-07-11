from sqlalchemy import inspect

from app.core.database import engine


def test_wiki_tables_exist():
    tables = set(inspect(engine).get_table_names())
    assert {"wiki_page", "wiki_link", "tag", "wiki_page_tag"} <= tables
