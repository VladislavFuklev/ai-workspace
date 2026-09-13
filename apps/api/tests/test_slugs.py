"""Slug generation — what ends up in a URL."""

from __future__ import annotations

import re

import pytest

from ai_workspace_api.core.slugs import MAX_LENGTH, slugify, unique_suffix

URL_SAFE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Acme", "acme"),
        ("Acme Legal", "acme-legal"),
        ("  Acme   Legal  ", "acme-legal"),
        ("ACME LEGAL", "acme-legal"),
        ("Acme & Co.", "acme-co"),
        ("Acme---Legal", "acme-legal"),
        ("Café Ltd", "cafe-ltd"),
        ("Ürgenç", "urgenc"),
        ("Acme 2026", "acme-2026"),
    ],
)
def test_latin_names_become_readable_slugs(name: str, expected: str) -> None:
    assert slugify(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Компанія", "kompaniia"),
        ("Юридична фірма", "iurydychna-firma"),
        ("Агенція Їжак", "ahentsiia-izhak"),
        ("ТОВ «Ґанок»", "tov-ganok"),
    ],
)
def test_cyrillic_names_transliterate(name: str, expected: str) -> None:
    """The product ships in Ukrainian. Without transliteration these produce an
    empty slug, and an organisation with no address."""
    assert slugify(name) == expected


@pytest.mark.parametrize(
    "name",
    ["Acme", "Компанія", "Café & Co.", "ТОВ «Ґанок»", "Ürgenç 2026"],
)
def test_every_slug_is_url_safe(name: str) -> None:
    assert URL_SAFE.match(slugify(name)), slugify(name)


@pytest.mark.parametrize("name", ["", "   ", "...", "!!! ???", "— – -"])
def test_a_name_with_nothing_usable_gives_an_empty_slug(name: str) -> None:
    """Empty rather than invented: a silently invented address is worse than a
    rejected input, and the caller is the one who can ask for another name."""
    assert slugify(name) == ""


def test_a_long_name_is_truncated_without_a_trailing_hyphen() -> None:
    slug = slugify("A very long organisation name " * 10)

    assert len(slug) <= MAX_LENGTH
    assert not slug.endswith("-")
    assert URL_SAFE.match(slug)


def test_the_suffix_is_short_and_unpredictable() -> None:
    """Not a counter: counting needs a query per attempt and tells anyone reading
    the URL how many organisations share a name."""
    suffixes = {unique_suffix() for _ in range(50)}

    assert all(len(s) == 4 and s.isalnum() for s in suffixes)
    assert len(suffixes) > 40, "suffixes are not random enough to avoid collisions"
