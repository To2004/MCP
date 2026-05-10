"""Generate the MCP Filesystem Tools teaching deck (18 slides)."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.slide import Slide
from pptx.util import Inches, Pt

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
BG = RGBColor(0x1E, 0x1E, 0x2E)       # dark navy background
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0x89, 0xB4, 0xFA)   # blue accent
GREEN = RGBColor(0xA6, 0xE3, 0xA1)    # good example
RED = RGBColor(0xF3, 0x8B, 0xA8)      # bad example / error
YELLOW = RGBColor(0xF9, 0xE2, 0xAF)   # warning / edge case
GRAY = RGBColor(0x45, 0x47, 0x5A)     # subtle box fill
MONO_FONT = "Courier New"
BODY_FONT = "Calibri"

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

OUTPUT = Path(__file__).parent.parent / "presentations" / "mcp-filesystem-tools.pptx"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def add_slide(prs: Presentation) -> Slide:
    """Add a blank slide and paint the background."""
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = BG
    return slide


def text_box(
    slide: Slide,
    left,
    top,
    width,
    height,
    text,
    size=Pt(18),
    bold=False,
    color=WHITE,
    font=BODY_FONT,
    align=PP_ALIGN.LEFT,
    wrap=True,
):
    """Add a text box and return the shape."""
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    return txb


def code_box(slide: Slide, left, top, width, height, code, fill=GRAY, text_color=WHITE):
    """A monospace code block with a filled background rectangle."""
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height,
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = fill

    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = code
    run.font.size = Pt(12)
    run.font.name = MONO_FONT
    run.font.color.rgb = text_color
    return shape


def label_box(
    slide: Slide,
    left,
    top,
    width,
    height,
    text,
    fill=ACCENT,
    text_color=BG,
    size=Pt(14),
):
    """Colored label / badge box."""
    shape = slide.shapes.add_shape(1, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = fill
    tf = shape.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = True
    run.font.name = BODY_FONT
    run.font.color.rgb = text_color
    return shape


def arrow(slide: Slide, x1, y1, x2, y2, color=ACCENT):
    """Draw a straight connector between two points."""
    connector = slide.shapes.add_connector(
        1,  # MSO_CONNECTOR_TYPE.STRAIGHT
        x1, y1, x2, y2,
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(2)
    return connector


def slide_title(slide: Slide, title, subtitle=None) -> None:
    """Add a slide title (large) and optional subtitle."""
    text_box(slide, Inches(0.5), Inches(0.2), Inches(12.3), Inches(0.9),
             title, size=Pt(32), bold=True, color=ACCENT)
    if subtitle:
        text_box(slide, Inches(0.5), Inches(1.0), Inches(12.3), Inches(0.5),
                 subtitle, size=Pt(18), color=WHITE)


# ---------------------------------------------------------------------------
# Slide stubs — replaced in Tasks 3, 4, 5
# ---------------------------------------------------------------------------

def _slide_01_title(prs: Presentation) -> None:
    slide = add_slide(prs)
    text_box(slide, Inches(1), Inches(2.2), Inches(11.3), Inches(1.5),
             "MCP Filesystem Server", size=Pt(48), bold=True, color=ACCENT,
             align=PP_ALIGN.CENTER)
    text_box(slide, Inches(1), Inches(3.7), Inches(11.3), Inches(0.8),
             "How It Works — Tool Reference & Teaching Guide",
             size=Pt(24), color=WHITE, align=PP_ALIGN.CENTER)
    text_box(slide, Inches(1), Inches(5.2), Inches(11.3), Inches(0.5),
             "@modelcontextprotocol/server-filesystem  v1.27.0",
             size=Pt(16), color=GRAY, align=PP_ALIGN.CENTER)


def _slide_02_what_is_mcp(prs: Presentation) -> None:
    slide = add_slide(prs)
    slide_title(slide, "What is MCP?",
                "Model Context Protocol — lets AI agents call tools on external servers")

    boxes = [
        (Inches(0.5),  "AI Agent",    ACCENT),
        (Inches(3.5),  "JSON-RPC 2.0", YELLOW),
        (Inches(6.5),  "MCP Server",   GREEN),
        (Inches(9.5),  "Filesystem",   GRAY),
    ]
    for left, label, color in boxes:
        label_box(slide, left, Inches(3.2), Inches(2.5), Inches(1.0),
                  label, fill=color, text_color=BG, size=Pt(16))

    for i in range(3):
        x1 = Inches(0.5 + i * 3 + 2.5)
        x2 = Inches(0.5 + (i + 1) * 3)
        arrow(slide, x1, Inches(3.7), x2, Inches(3.7))

    text_box(slide, Inches(0.5), Inches(4.5), Inches(12.3), Inches(1.2),
             "An agent sends a JSON-RPC request naming a tool (e.g. read_text_file) with "
             "parameters. The MCP server executes it and returns a result. "
             "The filesystem server exposes 13 tools — all sandboxed to an allowed root.",
             size=Pt(16), color=WHITE)


def _slide_03_request_response(prs: Presentation) -> None:
    slide = add_slide(prs)
    slide_title(slide, "Request → Response Flow")

    request_json = (
        '{\n'
        '  "jsonrpc": "2.0",\n'
        '  "id": 1,\n'
        '  "method": "tools/call",\n'
        '  "params": {\n'
        '    "name": "read_text_file",\n'
        '    "arguments": {\n'
        '      "path": "sensitive/security/audit_log.txt"\n'
        '    }\n'
        '  }\n'
        '}'
    )
    response_json = (
        '{\n'
        '  "jsonrpc": "2.0",\n'
        '  "id": 1,\n'
        '  "result": {\n'
        '    "content": [{\n'
        '      "type": "text",\n'
        '      "text": "2026-01-15 09:00 | LOGIN..."\n'
        '    }]\n'
        '  }\n'
        '}'
    )

    text_box(slide, Inches(0.5), Inches(1.5), Inches(5.5), Inches(0.4),
             "REQUEST", size=Pt(14), bold=True, color=GREEN)
    code_box(slide, Inches(0.5), Inches(1.9), Inches(5.5), Inches(4.8), request_json)

    arrow(slide, Inches(6.2), Inches(4.2), Inches(7.0), Inches(4.2))

    text_box(slide, Inches(7.2), Inches(1.5), Inches(5.5), Inches(0.4),
             "RESPONSE", size=Pt(14), bold=True, color=ACCENT)
    code_box(slide, Inches(7.2), Inches(1.9), Inches(5.5), Inches(4.8), response_json)


def _slide_04_security_boundary(prs: Presentation) -> None:
    slide = add_slide(prs)
    slide_title(slide, "The Security Boundary",
                "Every path must live inside the allowed root — no exceptions")

    root_box = slide.shapes.add_shape(1, Inches(0.5), Inches(1.8), Inches(6.0), Inches(4.5))
    root_box.fill.solid()
    root_box.fill.fore_color.rgb = RGBColor(0x1A, 0x2A, 0x1A)
    root_box.line.color.rgb = GREEN
    root_box.line.width = Pt(2)

    text_box(slide, Inches(0.7), Inches(1.9), Inches(5.5), Inches(0.4),
             "✓  Allowed root: /corp_filesystem/", size=Pt(14), bold=True, color=GREEN)

    allowed_paths = [
        "sensitive/security/audit_log.txt",
        "projects/known_defects.csv",
        "source_code/core.c",
    ]
    for i, path in enumerate(allowed_paths):
        text_box(slide, Inches(0.9), Inches(2.5 + i * 0.5), Inches(5.5), Inches(0.45),
                 f"  {path}", size=Pt(13), color=WHITE)

    blocked = [
        ("../etc/passwd",     "Access denied - path outside allowed directories"),
        ("C:/Windows/win.ini","Access denied - path outside allowed directories"),
        ("(empty string)",    "Access denied - path outside allowed directories"),
    ]
    for i, (attempt, error) in enumerate(blocked):
        y = Inches(2.1 + i * 1.1)
        label_box(slide, Inches(7.0), y, Inches(5.8), Inches(0.45),
                  f"✗  {attempt}", fill=RED, text_color=WHITE, size=Pt(12))
        text_box(slide, Inches(7.0), y + Inches(0.5), Inches(5.8), Inches(0.4),
                 f"→ {error}", size=Pt(11), color=RED)
def _slide_05_read_overview(prs): add_slide(prs)
def _slide_06_read_text_file(prs): add_slide(prs)
def _slide_07_read_media_file(prs): add_slide(prs)
def _slide_08_read_multiple_files(prs): add_slide(prs)
def _slide_09_write_tools(prs): add_slide(prs)
def _slide_10_list_tools(prs): add_slide(prs)
def _slide_11_search_files(prs): add_slide(prs)
def _slide_12_info_admin(prs): add_slide(prs)
def _slide_13_file_type_matrix(prs): add_slide(prs)
def _slide_14_glob_patterns(prs): add_slide(prs)
def _slide_15_path_pitfalls(prs): add_slide(prs)
def _slide_16_silent_overwrite(prs): add_slide(prs)
def _slide_17_partial_batch(prs): add_slide(prs)
def _slide_18_missing_tools(prs): add_slide(prs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_deck() -> Presentation:
    prs = new_presentation()
    _slide_01_title(prs)
    _slide_02_what_is_mcp(prs)
    _slide_03_request_response(prs)
    _slide_04_security_boundary(prs)
    _slide_05_read_overview(prs)
    _slide_06_read_text_file(prs)
    _slide_07_read_media_file(prs)
    _slide_08_read_multiple_files(prs)
    _slide_09_write_tools(prs)
    _slide_10_list_tools(prs)
    _slide_11_search_files(prs)
    _slide_12_info_admin(prs)
    _slide_13_file_type_matrix(prs)
    _slide_14_glob_patterns(prs)
    _slide_15_path_pitfalls(prs)
    _slide_16_silent_overwrite(prs)
    _slide_17_partial_batch(prs)
    _slide_18_missing_tools(prs)
    return prs


if __name__ == "__main__":
    prs = generate_deck()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUTPUT)
    print(f"Saved: {OUTPUT}")
