"""Smoke tests for the filesystem teaching deck generator."""

import pytest
from pptx.dml.color import RGBColor

from scripts.generate_filesystem_deck import generate_deck


@pytest.fixture(scope="session")
def deck():
    return generate_deck()


def test_deck_has_18_slides(deck):
    assert len(deck.slides) == 18


def test_slide_backgrounds_are_dark(deck):
    for i, slide in enumerate(deck.slides):
        fill = slide.background.fill
        assert fill.fore_color.rgb == RGBColor(0x1E, 0x1E, 0x2E), f"Slide {i+1} wrong bg"
