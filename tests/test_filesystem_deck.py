"""Smoke tests for the filesystem teaching deck generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_filesystem_deck import generate_deck


def test_deck_has_18_slides():
    prs = generate_deck()
    assert len(prs.slides) == 18


def test_slide_backgrounds_are_dark():
    from pptx.dml.color import RGBColor
    prs = generate_deck()
    for i, slide in enumerate(prs.slides):
        fill = slide.background.fill
        assert fill.fore_color.rgb == RGBColor(0x1E, 0x1E, 0x2E), f"Slide {i+1} wrong bg"
