from app.modules.wiki.links import extract_wikilinks, render_markdown, slugify


def test_slugify_basic():
    assert slugify("The Sunless Citadel!") == "the-sunless-citadel"


def test_slugify_empty_falls_back():
    assert slugify("   ") == "page"


def test_extract_dedupes_and_preserves_order():
    assert extract_wikilinks("[[Bravo]] and [[Alpha]] and [[bravo]]") == ["Bravo", "Alpha"]


def test_extract_ignores_code():
    body = "See [[Real]].\n\n```\n[[NotALink]]\n```\n\nand `[[AlsoNot]]` inline"
    assert extract_wikilinks(body) == ["Real"]


def test_extract_handles_none():
    assert extract_wikilinks(None) == []


def _resolver(name):
    # 'Known' resolves; anything else does not.
    return ("/wiki/known", True) if name == "Known" else ("/wiki/new?title=x", False)


def test_render_resolved_link():
    html = render_markdown("Go to [[Known]] now", _resolver)
    assert 'href="/wiki/known"' in html
    assert 'class="wikilink"' in html
    assert "Known" in html


def test_render_unresolved_link_gets_new_class():
    html = render_markdown("Go to [[Ghost]] now", _resolver)
    assert "wikilink-new" in html


def test_render_leaves_code_literal():
    html = render_markdown("```\n[[Known]]\n```", _resolver)
    assert "wikilink" not in html
    assert "[[Known]]" in html


def test_render_markdown_formats():
    html = render_markdown("**bold**", _resolver)
    assert "<strong>bold</strong>" in html
