from tooling.docs.check_links import find_violations


def test_repository_local_markdown_links_resolve() -> None:
    assert find_violations() == []
