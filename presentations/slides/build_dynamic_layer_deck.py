"""Generate 2026-10-19_dynamic-layer-lenovo.pptx on the Lenovo template.

Content: reports/experiments/dynamic_dimensions/FORMULA.md (three questions and the e formula) and
SCENARIOS.md (15 scenarios and the two new ideas). Every number is copied from those two files.
The template's sample slides are removed; its layouts, footer and logo are kept.

Run:  python build_dynamic_layer_deck.py
"""

import copy
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).parent
TEMPLATE = HERE / "2026-04-28_lenovo-template.pptx"
OUT = HERE / "2026-10-19_dynamic-layer-lenovo.pptx"

# Lenovo template theme colours (theme1.xml) plus the card tints used in the static-scanner deck
NAVY, RED, CORAL, PLUM = "11184F", "E1251B", "F26A52", "4D144A"
LILAC, PERI, GRAY, INK = "D9C1D8", "C9D0F0", "4E444E", "1E1B24"
CARD, CARD2, WHITE, GREEN, MUTED = "F5F3F5", "EFECF1", "FFFFFF", "2E8B57", "6B6470"
SOFT_RED, SOFT_GREEN = "FBE3E1", "E3F1E8"
FAMILY = {"Pace": CORAL, "Path": NAVY, "Place": PLUM}

LEFT, RIGHT, TOP, BOTTOM = 0.83, 12.5, 1.45, 6.75
WIDTH = RIGHT - LEFT


def rgb(hex_: str) -> RGBColor:
    return RGBColor.from_string(hex_)


# ── deck plumbing ──────────────────────────────────────────────────────────────
def open_template() -> Presentation:
    """The Lenovo template with its sample slides removed (layouts, footer and logo kept)."""
    prs = Presentation(str(TEMPLATE))
    ids = prs.slides._sldIdLst
    for sld in list(ids):
        prs.part.drop_rel(sld.rId)
        ids.remove(sld)
    return prs


def layout(prs: Presentation, name: str):
    for lay in prs.slide_masters[0].slide_layouts:
        if lay.name == name:
            return lay
    raise KeyError(name)


def add_slide_number(slide) -> None:
    """python-pptx does not copy the slide-number placeholder; copy it from the layout."""
    for ph in slide.slide_layout.placeholders:
        if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
            slide.shapes._spTree.append(copy.deepcopy(ph._element))
            return


def new_slide(prs, layout_name: str, title: str, notes: str, number: bool = True):
    slide = prs.slides.add_slide(layout(prs, layout_name))
    if slide.shapes.title is not None:
        slide.shapes.title.text_frame.text = title
    slide.notes_slide.notes_text_frame.text = notes
    if number:
        add_slide_number(slide)
    return slide


# ── drawing helpers ────────────────────────────────────────────────────────────
def box(slide, x, y, w, h, fill=CARD, radius=0.06, line=None, name="Card"):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                                   Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        shape.adjustments[0] = radius
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    shape.name = name
    shape.text_frame.text = ""
    return shape


def text(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, margin=0.0, name="Text"):
    """paras: list of dicts {t | runs, size, bold, color, align, after, italic}."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(margin))
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        para.space_after = Pt(p.get("after", 4))
        runs = p.get("runs") or [(p["t"], {})]
        for run_text, opts in runs:
            r = para.add_run()
            r.text = run_text
            f = r.font
            f.size = Pt(opts.get("size", p.get("size", 14)))
            f.bold = opts.get("bold", p.get("bold", False))
            f.italic = opts.get("italic", p.get("italic", False))
            f.color.rgb = rgb(opts.get("color", p.get("color", INK)))
    return tb


def circle(slide, x, y, d, label, fill=RED, size=14):
    c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    c.fill.solid()
    c.fill.fore_color.rgb = rgb(fill)
    c.line.fill.background()
    c.shadow.inherit = False
    c.name = f"Step {label}"
    tf = c.text_frame
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(0))
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(label)
    r.font.size, r.font.bold, r.font.color.rgb = Pt(size), True, rgb(WHITE)
    return c


def chip(slide, x, y, w, label, fill, size=13, h=0.36):
    s = box(slide, x, y, w, h, fill=fill, radius=0.5, name=f"Chip {label}")
    tf = s.text_frame
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size, r.font.bold, r.font.color.rgb = Pt(size), True, rgb(WHITE)
    return s


def table(slide, x, y, col_w, rows, size=12, header_fill=NAVY, row_h=0.36, fills=None, bold_first=True):
    """rows[0] is the header. fills: {row_index: hex} for highlighted body rows."""
    fills = fills or {}
    n_r, n_c = len(rows), len(rows[0])
    gf = slide.shapes.add_table(n_r, n_c, Inches(x), Inches(y), Inches(sum(col_w)), Inches(row_h * n_r))
    gf.name = "Table"
    tbl = gf.table
    tbl.horz_banding = False
    tbl.first_row = True
    for j, w in enumerate(col_w):
        tbl.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(header_fill if i == 0 else fills.get(i, WHITE if i % 2 else CARD))
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.size = Pt(size)
            r.font.bold = i == 0 or (bold_first and j == 0)
            r.font.color.rgb = rgb(WHITE if i == 0 else INK)
    return tbl


def bar_chart(slide, x, y, w, h, categories, series, colors, label_size=12, max_v=100, legend=True,
              point_colors=None, gap=55):
    data = CategoryChartData()
    data.categories = categories
    for name, values in series.items():
        data.add_series(name, values)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h),
                                data)
    gf.name = "Chart"
    ch = gf.chart
    ch.has_title = False
    ch.font.size = Pt(label_size)
    ch.font.color.rgb = rgb(GRAY)
    ch.has_legend = legend and len(series) > 1
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(label_size)
    plot = ch.plots[0]
    plot.gap_width = gap
    plot.overlap = -5 if len(series) > 1 else 0
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = '0"%"'
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(label_size)
    dl.font.color.rgb = rgb(INK)
    for s, color in zip(plot.series, colors):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(color)
    if point_colors:
        for pt, color in zip(plot.series[0].points, point_colors):
            pt.format.fill.solid()
            pt.format.fill.fore_color.rgb = rgb(color)
    va = ch.value_axis
    va.maximum_scale, va.minimum_scale = max_v, 0
    va.has_major_gridlines = False
    va.visible = False
    ca = ch.category_axis
    ca.reverse_order = True
    ca.tick_labels.font.size = Pt(label_size)
    ca.tick_labels.font.color.rgb = rgb(INK)
    ca.format.line.color.rgb = rgb(LILAC)
    ca.has_major_gridlines = False
    return ch


def stat(slide, x, y, w, h, big, label, color=RED, fill=CARD, big_size=40, label_size=14):
    box(slide, x, y, w, h, fill=fill, name="Stat card")
    text(slide, x + 0.25, y + 0.1, w - 0.5, 0.7, [{"t": big, "size": big_size, "bold": True, "color": color}],
         anchor=MSO_ANCHOR.MIDDLE)
    text(slide, x + 0.25, y + 0.85, w - 0.5, h - 0.95, [{"t": label, "size": label_size, "color": INK}])


# ── slides ─────────────────────────────────────────────────────────────────────
def s_title(prs):
    s = prs.slides.add_slide(layout(prs, "Title Slide_Black"))
    s.shapes.title.text_frame.text = "The dynamic layer: three questions, one formula"
    s.placeholders[1].text_frame.text = "Runtime risk for MCP servers  |  Tomer Ovadya  |  October 2026"
    s.notes_slide.notes_text_frame.text = (
        "This deck covers two documents: FORMULA.md (the three questions and the e formula) and "
        "SCENARIOS.md (15 scenarios and two new ideas). All numbers come from simulated organisations "
        "built from real calls and the real static scan.")


def s_what(prs):
    s = new_slide(prs, "Title Only", "What the dynamic layer adds to the static score",
                  "Static answers how much damage a tool can do, once, at design time. Dynamic answers how "
                  "strange this call is for this agent right now. The result multiplies the static score and "
                  "never lowers it. It reads only the request side, never inputs, assets or responses.")
    cards = [("Static layer", "design time", "How much damage can this tool do?",
              "One score per tool from the scan (impact 1–5)", NAVY),
             ("Dynamic layer", "runtime", "How strange is this call, for this agent, right now?",
              "A multiplier from ×1 (normal) to ×8", RED)]
    for i, (name, when, q, out, color) in enumerate(cards):
        x = LEFT + i * 5.95
        box(s, x, TOP, 5.75, 2.55)
        text(s, x + 0.3, TOP + 0.25, 5.2, 0.45, [{"runs": [(name, {"bold": True, "size": 20, "color": color}),
                                                           (f"   {when}", {"size": 14, "color": MUTED})]}])
        text(s, x + 0.3, TOP + 0.85, 5.2, 0.9, [{"t": q, "size": 18, "bold": True}])
        text(s, x + 0.3, TOP + 1.8, 5.2, 0.5, [{"t": out, "size": 14, "color": GRAY}])
    box(s, LEFT, 4.25, WIDTH, 0.8, fill=NAVY, name="Formula strip")
    text(s, LEFT, 4.25, WIDTH, 0.8, [{"runs": [("R_dynamic  =  R_static  ×  multiplier", {"bold": True, "size": 22,
                                                                                        "color": WHITE}),
                                               ("      never below the static score", {"size": 14,
                                                                                       "color": PERI})],
                                      "align": PP_ALIGN.CENTER}], anchor=MSO_ANCHOR.MIDDLE)
    reads = [("Reads", ["The tool name and whether it reads, writes or removes",
                        "Time and volume", "A general client: client family, /16 network range"], GREEN),
             ("Never reads", ["Tool inputs or the specific asset", "Server responses",
                              "Anything not stated in the policy"], RED)]
    for i, (head, items, color) in enumerate(reads):
        x = LEFT + i * 5.95
        text(s, x, 5.3, 5.75, 0.4, [{"t": head, "size": 15, "bold": True, "color": color}])
        text(s, x, 5.7, 5.75, 1.1, [{"runs": [("✓  " if color == GREEN else "✕  ", {"bold": True, "color": color}),
                                             (it, {})], "size": 14, "after": 2} for it in items])


def s_three(prs):
    s = new_slide(prs, "Title Only", "Three questions about every call",
                  "Each question compares the agent with its own last 90 days. Pace is close to deviation, "
                  "Path to access anomaly at tool level, Place to novelty. Alone each catches 16–29%; together "
                  "50–58%, because they see different things.")
    fams = [("Pace", "Is it doing this more or faster than usual?", "Same tool repeated within 10 minutes",
             "Loops, page walks, bursts, storms", "Deviation", "20% / 22%"),
            ("Path", "Is it doing something it does not usually do?",
             "Unusual next step: this tool right after the previous one",
             "Off-role tools, skipped steps, slow scope creep", "Access anomaly", "25% / 29%"),
            ("Place", "Is it coming from somewhere new?", "New network range (/16), new client family",
             "New origin, shared credential, client switch", "Novelty", "16% / 16%")]
    cw = (WIDTH - 2 * 0.3) / 3
    for i, (name, q, dims, catches, close, alone) in enumerate(fams):
        x = LEFT + i * (cw + 0.3)
        color = FAMILY[name]
        box(s, x, TOP, cw, 4.45)
        chip(s, x + 0.3, TOP + 0.3, 1.15, name, color, size=15, h=0.42)
        text(s, x + 1.6, TOP + 0.33, cw - 1.75, 0.4, [{"t": f"close to: {close}", "size": 11, "color": MUTED}],
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, x + 0.3, TOP + 0.95, cw - 0.6, 1.0, [{"t": q, "size": 18, "bold": True}])
        text(s, x + 0.3, TOP + 2.0, cw - 0.6, 1.6, [
            {"t": "Dimension", "size": 12, "bold": True, "color": color, "after": 1},
            {"t": dims, "size": 14, "after": 8},
            {"t": "Catches", "size": 12, "bold": True, "color": color, "after": 1},
            {"t": catches, "size": 14}])
        text(s, x + 0.3, TOP + 3.8, cw - 0.6, 0.45, [{"runs": [("Alone  ", {"size": 12, "color": MUTED}),
                                                              (alone, {"size": 16, "bold": True})]}])
    box(s, LEFT, 6.1, WIDTH, 0.65, fill=CARD2, name="Together")
    text(s, LEFT + 0.3, 6.1, WIDTH - 0.6, 0.65, [{"runs": [("All three together:  ", {"size": 15}),
                                                          ("50% / 58%", {"size": 18, "bold": True, "color": RED}),
                                                          ("   detection at ≤ 2 / ≤ 4 flagged agent-days a day",
                                                           {"size": 13, "color": MUTED})]}],
         anchor=MSO_ANCHOR.MIDDLE)


def s_formula(prs):
    s = new_slide(prs, "Title Only", "The formula",
                  "Five steps. Surprise against the agent's own history; a normal level learned from the "
                  "organisation's month; only the excess above normal counts and it is never negative; each "
                  "family counted once; then e to the lambda times the sum. Lambda only changes the number "
                  "shown, not who is flagged.")
    box(s, LEFT, TOP, WIDTH, 1.05, fill=NAVY, name="Formula")
    text(s, LEFT, TOP, WIDTH, 1.05, [{"runs": [("R_dynamic  =  R_static  ×  e", {"size": 26, "bold": True,
                                                                               "color": WHITE}),
                                              ("^( λ · (X_pace + X_path + X_place) )", {"size": 22, "bold": True,
                                                                                        "color": WHITE}),
                                              ("     at most ×8", {"size": 14, "color": PERI})],
                                     "align": PP_ALIGN.CENTER}], anchor=MSO_ANCHOR.MIDDLE)
    steps = [("Surprise", "u = −log₂ p", "p = how often this agent did this in its last 90 days. A new agent "
              "borrows its team's habit."),
             ("Normal level", "B", "The surprise only 0.5% of the organisation's calls reached in 30 days, "
              "per dimension."),
             ("Excess", "x = max(0, u − B)", "Only the part above normal counts. Never negative."),
             ("One per family", "X = largest x", "A new network that brings a new client counts once."),
             ("Multiply", "e^(λ · ΣX)", "λ = ln 2 / 10: every 10 bits above normal doubles the risk.")]
    sw, gap = (WIDTH - 4 * 0.2) / 5, 0.2
    for i, (name, f, desc) in enumerate(steps):
        x = LEFT + i * (sw + gap)
        box(s, x, 2.8, sw, 2.85)
        circle(s, x + 0.2, 2.98, 0.48, i + 1)
        text(s, x + 0.8, 2.98, sw - 0.9, 0.48, [{"t": name, "size": 15, "bold": True}], anchor=MSO_ANCHOR.MIDDLE)
        text(s, x + 0.2, 3.65, sw - 0.4, 0.55, [{"t": f, "size": 15, "bold": True, "color": RED}])
        text(s, x + 0.2, 4.25, sw - 0.4, 1.35, [{"t": desc, "size": 13, "color": GRAY}])
    text(s, LEFT, 5.9, WIDTH, 0.85, [
        {"runs": [("Daily check  ", {"bold": True, "color": NAVY}),
                  ("An agent's day score is the sum of each family's strongest call. Flag the agent-days above a "
                   "threshold set by how many the team can review, and never below 4 bits.", {})],
         "size": 14}])


def s_example(prs):
    s = new_slide(prs, "Title Only", "One call, worked through",
                  "Illustrative numbers. A release agent makes a step it never made in 90 days: Path excess 12 "
                  "bits, multiplier 2.3, so a static 4 shows 9.2. If the same call also comes from a new network "
                  "and a new client, Place adds 11 bits once, multiplier 4.9, shown risk 19.7.")
    text(s, LEFT, TOP, WIDTH, 0.5, [{"runs": [("A release agent calls ", {}), ("create_release", {"bold": True}),
                                              (" right after ", {}), ("search_code", {"bold": True}),
                                              (": a step it has never made in 90 days.", {}),
                                              ("   (illustrative numbers)", {"size": 12, "color": MUTED})],
                                     "size": 16}])
    cases = [("The step alone", [("Path", "16 − 4 = 12 bits"), ("Pace", "0"), ("Place", "0")],
              "e^(0.069 × 12) = ×2.3", "4  →  9.2"),
             ("Also from a new network and a new client",
              [("Path", "12 bits"), ("Pace", "0"), ("Place", "max(11, 11) = 11 bits, counted once")],
              "e^(0.069 × 23) = ×4.9", "4  →  19.7")]
    for i, (head, fams, mult, risk) in enumerate(cases):
        x = LEFT + i * 5.95
        box(s, x, 2.15, 5.75, 4.55)
        text(s, x + 0.3, 2.35, 5.2, 0.45, [{"t": head, "size": 17, "bold": True}])
        for j, (fam, val) in enumerate(fams):
            yy = 2.95 + j * 0.55
            chip(s, x + 0.3, yy, 1.05, fam, FAMILY[fam], size=12, h=0.34)
            text(s, x + 1.5, yy - 0.02, 4.0, 0.4, [{"t": val, "size": 15}], anchor=MSO_ANCHOR.MIDDLE)
        text(s, x + 0.3, 4.75, 5.2, 0.4, [{"runs": [("Multiplier   ", {"size": 13, "color": MUTED}),
                                                     (mult, {"size": 16, "bold": True})]}])
        text(s, x + 0.3, 5.3, 5.2, 1.2, [{"runs": [("Risk shown  ", {"size": 13, "color": MUTED}),
                                                    (risk, {"size": 36, "bold": True, "color": RED})]}],
             anchor=MSO_ANCHOR.MIDDLE)


def s_why(prs):
    s = new_slide(prs, "Title Only", "Why this form: tested against the alternatives",
                  "Same four dimensions, 9 organisations, mean over 21 kinds. Subtracting the normal level is "
                  "what makes adding safe: a just-above-normal value adds almost nothing, and on 95% of ordinary "
                  "days at most one family is above normal. After it, adding, multiplying or taking the largest "
                  "give the same result.")
    cats = ["New e formula (excess, add)", "Strongest signal (\"1 in N\")", "Earlier two-threshold rule",
            "Deck form e^(B − L)", "CARMA product, no org comparison", "\"1 in N\", add"]
    bar_chart(s, LEFT - 0.1, TOP - 0.05, 7.6, 5.35, cats,
              {"≤ 2 flagged agent-days a day": [50, 49, 41, 42, 42, 35],
               "≤ 4 flagged agent-days a day": [58, 57, 53, 51, 51, 54]}, [NAVY, CORAL], label_size=12)
    box(s, 8.75, TOP, 3.75, 5.25, fill=CARD)
    text(s, 9.0, TOP + 0.25, 3.3, 4.9, [
        {"t": "Subtracting the normal level is what makes adding safe", "size": 18, "bold": True,
         "color": NAVY, "after": 12},
        {"t": "Without it, two mild oddities add up and outrank one truly rare thing.", "size": 14,
         "after": 10},
        {"t": "With it, a just-above-normal value adds almost 0.", "size": 14, "after": 10},
        {"t": "Then add, multiply or take the largest: all three give 50% / 58%.", "size": 14,
         "after": 10},
        {"t": "λ and the ×8 cap change only the number shown, not who is flagged.", "size": 14,
         "color": GRAY}])


def s_kinds(prs):
    s = new_slide(prs, "Title Only", "What it catches, and what it cannot see",
                  "Detection by kind at up to 4 flagged agent-days a day, four dimensions. The bottom group is "
                  "not visible without looking inside the call: it needs the request size, an asset-name hash, "
                  "or working hours from the policy.")
    kinds = [("New origin", 100), ("Off-role tool", 99), ("Shared credential", 97), ("Page walk", 92),
             ("Client switch", 89), ("Slow creep", 89), ("Repeated habit", 76), ("Recipient blast", 72),
             ("Workflow skip", 65), ("Mode switch", 64), ("Dormant wake", 63), ("Loop", 62), ("Long span", 58),
             ("Burst", 55), ("Cancel storm", 51), ("Content dump", 24), ("Protocol skip", 23), ("Fan-out", 18),
             ("Over-fetch", 7), ("Off-hours", 6), ("Sensitive asset", 3)]
    colors = [NAVY if v >= 85 else CORAL if v >= 55 else PLUM if v >= 45 else LILAC for _, v in kinds]
    bar_chart(s, LEFT - 0.1, TOP - 0.15, 7.4, 5.5, [k for k, _ in kinds], {"Detection": [v for _, v in kinds]},
              [NAVY], label_size=11, legend=False, point_colors=colors, gap=35)
    legend = [(NAVY, "Very high", "85% and above"), (CORAL, "Good", "55–85%"), (PLUM, "Fair", "about 50%"),
              (LILAC, "Not visible at this level", "below 25%")]
    for i, (c, name, rng) in enumerate(legend):
        yy = TOP + i * 0.55
        box(s, 8.6, yy + 0.08, 0.3, 0.3, fill=c, radius=0.2, name="Legend swatch")
        text(s, 9.05, yy, 3.4, 0.45, [{"runs": [(name, {"bold": True}), (f"   {rng}", {"color": MUTED})],
                                       "size": 13}], anchor=MSO_ANCHOR.MIDDLE)
    box(s, 8.6, 3.85, 3.9, 2.35, fill=CARD)
    text(s, 8.85, 4.0, 3.45, 2.15, [
        {"t": "To see the bottom group", "size": 15, "bold": True, "color": NAVY, "after": 8},
        {"t": "Over-fetch, content dump → request size in bytes", "size": 13, "after": 6},
        {"t": "Fan-out, sensitive asset → a hash of the asset name", "size": 13, "after": 6},
        {"t": "Off-hours → working hours written in the policy", "size": 13}])


def s_sources(prs):
    s = new_slide(prs, "Title Only", "Built on earlier work, changed where the tests said so",
                  "The e form and the per-feature baseline come from the methodology deck; the three families, "
                  "max inside a family and never-below-static from CARMA. Changes were driven by tests: surprise "
                  "instead of support share, a learned baseline, no discount, fixed windows.")
    rows = [["Source", "Kept", "Changed, and why"],
            ["Methodology deck, e^(λ(B − L))", "The e form; a baseline per feature",
             "Support share → surprise (keeps 1 in 100 apart from 1 in 100,000); B learned, not set; "
             "clamped at 0, no discount; fixed windows fix aging"],
            ["CARMA, R_static × D × A × N", "Three families; strongest inside each; never below static; "
             "team fill-in", "Families redefined for the high level; σ cap replaced by excess over normal"],
            ["Hyndman & Frazier 2026", "Surprise (−log p); count it in everyone's tail", "B is that tail point"],
            ["Kriegel et al. 2011", "One scale before combining detectors", "Bits above each dimension's normal"],
            ["Heard & Rubin-Delanchy 2018", "Adding surprises = Fisher; the largest = Tippett",
             "The normal level gives the benefit of both"],
            ["Splunk, Exabeam, Sentinel, Elastic", "Risk added per entity per day; scores against own history",
             "Same daily check and baseline idea"]]
    table(s, LEFT, TOP, [3.2, 3.6, 4.87], rows, size=12, row_h=0.72)


def s_section(prs):
    s = prs.slides.add_slide(layout(prs, "Section Header_Black"))
    s.shapes.title.text_frame.text = "Scenarios and two new ideas"
    s.placeholders[1].text_frame.text = "15 concrete cases run through a reference engine"
    add_slide_number(s)
    s.notes_slide.notes_text_frame.text = (
        "Second half: the formula run on concrete scenarios by an actual implementation, where it breaks, "
        "and two new ideas that fix the breaks.")


def s_setup(prs):
    s = new_slide(prs, "Title Only", "15 scenarios on one simulated organisation",
                  "Every number in this half comes from running the reference engine, not hand calculation. "
                  "One GitHub organisation with real tool names and static impacts. Each scenario starts on day "
                  "70. The daily check uses a budget of 2 a day with the threshold from the previous 30 days and "
                  "a floor of 4 bits.")
    stats = [("50", "agents: 16 reviewers, 16 developers, 8 triagers, 10 merge bots"),
             ("90", "days; each scenario starts on day 70"),
             ("26", "real GitHub tools with static impacts from the reference scan"),
             ("2 / day", "review budget; threshold from the previous 30 days, floor 4 bits")]
    cw = (WIDTH - 0.3) / 2
    for i, (big, label) in enumerate(stats):
        x = LEFT + (i % 2) * (cw + 0.3)
        y = TOP + (i // 2) * 1.75
        stat(s, x, y, cw, 1.55, big, label, color=RED if i < 3 else NAVY, big_size=36, label_size=14)
    box(s, LEFT, 5.1, WIDTH, 1.65, fill=CARD2)
    text(s, LEFT + 0.3, 5.25, WIDTH - 0.6, 1.4, [
        {"t": "Reported per scenario", "size": 15, "bold": True, "color": NAVY, "after": 6},
        {"t": "The strongest call (multiplier, risk before → after), which family fired, whether the day was "
              "flagged, and for organisation-wide scenarios how many alerts the organisation received.",
         "size": 14}])


def s_single(prs):
    s = new_slide(prs, "Title Only", "Single-agent cases are caught on the day",
                  "Off-role steps, shared credentials, new places, loops and creep stand out the day they happen. "
                  "Team fill-in is what catches a new hire's mistake on day 1. Over-fetching is invisible because "
                  "the calls look identical without reading inputs. A repeated daily merge is learned after two "
                  "days: good for real habits, a blind spot for repeated misuse.")
    rows = [["Scenario", "Family", "Strongest call", "Flagged"],
            ["Loop: the same read 40 more times in 8 min", "Pace 4.8", "3 → 4.2 (×1.39)", "yes"],
            ["Off-role step: a reviewer merges", "Path 12.5", "4 → 9.5 (×2.38)", "yes"],
            ["Shared credential: 3 new networks + new client", "Place 9.8", "2 → 3.9 (×1.97)", "yes"],
            ["Off-role step from a new place", "Path 12.5 + Place 9.2", "day score 21.7", "yes"],
            ["Slow creep: a new write tool each day", "Path ≈ 12 a day", "4 → 9.7", "every working day"],
            ["Same off-role step daily", "Path 12.5 on day 1", "4 → 9.5", "first 2 of 8 days"],
            ["Nagging loop: 12 extra list calls a day", "Path 10.8", "2 → 4.2", "all 5 working days"],
            ["New hire, normal work", "none in week 1", "×1.0", "no"],
            ["New hire merges on day 1 (team fill-in)", "Path 7.2", "4 → 6.6 (×1.64)", "yes"],
            ["Same, without team fill-in", "none", "×1.0", "missed"],
            ["Over-fetch: same calls, bigger pages", "none", "×1.0", "not visible"]]
    table(s, LEFT, TOP - 0.05, [5.0, 2.45, 2.25, 1.97], rows, size=12, row_h=0.43,
          fills={10: SOFT_RED, 11: SOFT_RED})


def s_breaks(prs):
    s = new_slide(prs, "Title Only", "Where the base formula breaks",
                  "Organisation-wide changes flood the review budget: each agent looks strange but nobody "
                  "misbehaved. A legitimate role change keeps alerting because the 90-day history is still full "
                  "of the old role. Neither can be fixed by looking at one agent.")
    cards = [("38 alerts", "in 3 days", "Client rollout: all 40 people switch to a new client (legitimate)"),
             ("40 alerts", "in one day", "Server slowdown: everyone retries the same read in the same hour"),
             ("7 of 15", "working days", "Role change: a reviewer becomes a developer (legitimate)")]
    cw = (WIDTH - 2 * 0.3) / 3
    for i, (big, unit, label) in enumerate(cards):
        x = LEFT + i * (cw + 0.3)
        box(s, x, TOP, cw, 2.7)
        text(s, x + 0.3, TOP + 0.2, cw - 0.6, 2.4, [{"t": big, "size": 40, "bold": True, "color": RED, "after": 0},
                                                   {"t": unit, "size": 15, "color": MUTED, "after": 12},
                                                   {"t": label, "size": 15}])
    box(s, LEFT, 4.4, WIDTH, 1.1, fill=NAVY, name="Message")
    text(s, LEFT + 0.35, 4.4, WIDTH - 0.7, 1.1, [
        {"t": "Nobody misbehaved: the organisation, the server or the job changed. One agent's history "
              "cannot tell. The first needs the other agents; the second needs time.", "size": 16,
         "bold": True, "color": WHITE}], anchor=MSO_ANCHOR.MIDDLE)
    text(s, LEFT, 5.75, WIDTH, 1.0, [
        {"runs": [("Also weak  ", {"bold": True, "color": NAVY}),
                  ("Pace says \"more than ever before\", not \"how much more\": a 40-times loop scores only ×1.39. "
                   "Over-fetching is invisible when inputs are not read.", {})], "size": 14}])


def before_after(s, x, y, w, label, before, after, h=1.25):
    box(s, x, y, w, h, fill=CARD)
    text(s, x + 0.25, y + 0.12, w - 0.5, 0.4, [{"t": label, "size": 14, "bold": True}])
    left_w = (w - 0.5) * 0.36
    text(s, x + 0.25, y + 0.52, left_w, h - 0.6, [{"runs": [("before  ", {"size": 12, "color": MUTED}),
                                                           (before, {"size": 16, "bold": True, "color": RED})]}],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.25 + left_w, y + 0.52, w - 0.5 - left_w, h - 0.6,
         [{"runs": [("after  ", {"size": 12, "color": MUTED}),
                    (after, {"size": 16, "bold": True, "color": GREEN})]}], anchor=MSO_ANCHOR.MIDDLE)


def steps_list(s, x, y, w, items, gap=0.78, size=14):
    for i, t in enumerate(items):
        yy = y + i * gap
        circle(s, x, yy, 0.42, i + 1, size=13)
        text(s, x + 0.6, yy - 0.04, w - 0.6, gap, [{"t": t, "size": size}])


def s_crowd(prs):
    s = new_slide(prs, "Title Only", "Idea A, crowd: one agent, or everyone?",
                  "When many agents do the same strange thing at the same time, the cause is shared: a rollout, "
                  "an outage, a new tool. Once 5 or more agents clearly share it, it becomes one notice for the "
                  "organisation and stops counting for each agent. This flips peer comparison: peer tools look "
                  "for the odd one out; here a change made together belongs to the organisation.")
    text(s, LEFT, TOP, 5.6, 0.5, [{"t": "How it works", "size": 16, "bold": True, "color": NAVY}])
    steps_list(s, LEFT, TOP + 0.6, 5.6, [
        "A thing is the same step, the same tool in the same hour, or the same new network or client.",
        "Count the agents clearly above normal on it (X ≥ 3 bits), up to the end of the day.",
        "5 or more agents: one notice for the organisation; it stops counting for each of them.",
        "Below 5 nothing changes: a credential shared by 2 people still alerts on both."], gap=0.88)
    x = 6.9
    before_after(s, x, TOP, 5.6, "Client rollout (3 days)", "38 alerts", "2 alerts + 1 notice a day")
    before_after(s, x, TOP + 1.45, 5.6, "Server slowdown (1 day)", "40 alerts", "0 alerts + 2 notices")
    before_after(s, x, TOP + 2.9, 5.6, "All single-agent scenarios", "caught", "no change")
    box(s, LEFT, 5.85, WIDTH, 0.9, fill=CARD2)
    text(s, LEFT + 0.3, 5.85, WIDTH - 0.6, 0.9, [
        {"runs": [("Cost  ", {"bold": True, "color": RED}),
                  ("If 5 or more agents misbehave the same way at once (one bad prompt template), it shows as one "
                   "organisation notice instead of 5 agent alerts: still visible, as a single item.", {})],
         "size": 14}], anchor=MSO_ANCHOR.MIDDLE)


def s_settle(prs):
    s = new_slide(prs, "Title Only", "Idea B, settling: changed, or misbehaving?",
                  "A legitimate change settles: the agent does the new thing again and again. Misuse is usually a "
                  "one-off or keeps changing. A step made on 3 or more of the last 7 days is a new habit, so its "
                  "Path excess is 0. Repeated daily misuse alerts only on its first days, no worse than the base "
                  "formula, which also learns a habit within a few days.")
    box(s, LEFT, TOP, 5.6, 4.1, fill=NAVY, name="Idea")
    text(s, LEFT + 0.35, TOP + 0.3, 4.9, 3.6, [
        {"t": "The idea", "size": 14, "bold": True, "color": PERI, "after": 6},
        {"t": "A legitimate change settles: the agent does the new thing again and again.", "size": 18,
         "bold": True, "color": WHITE, "after": 14},
        {"t": "The rule", "size": 14, "bold": True, "color": PERI, "after": 6},
        {"t": "A step made on at least 3 different days of the last 7 is a new habit: its Path excess is 0.",
         "size": 16, "color": WHITE}])
    used = {1, 2, 4}
    for d in range(7):
        dx = LEFT + 0.35 + d * 0.66
        box(s, dx, TOP + 2.95, 0.54, 0.54, fill=CORAL if d in used else NAVY, line=PERI, radius=0.15,
            name=f"Day {d + 1}")
        text(s, dx, TOP + 2.95, 0.54, 0.54, [{"t": "MTWTFSS"[d], "size": 13, "bold": True, "color": WHITE,
                                             "align": PP_ALIGN.CENTER}], anchor=MSO_ANCHOR.MIDDLE)
    text(s, LEFT + 0.35, TOP + 3.55, 4.9, 0.45, [{"t": "Used on 3 of the last 7 days → a habit", "size": 13,
                                                 "color": PERI}])
    x = 6.9
    before_after(s, x, TOP, 5.6, "Role change (legitimate): working days flagged", "7 of 15", "5 of 15")
    before_after(s, x, TOP + 1.45, 5.6, "Slow creep, a new tool each day: days flagged", "8 of 8",
                 "8 of 8 (nothing repeats)")
    before_after(s, x, TOP + 2.9, 5.6, "Same off-role step daily: days flagged", "2 of 8",
                 "2 of 8 (already learned)")
    box(s, LEFT, 5.85, WIDTH, 0.9, fill=CARD2)
    text(s, LEFT + 0.3, 5.85, WIDTH - 0.6, 0.9, [
        {"runs": [("Cost  ", {"bold": True, "color": RED}),
                  ("Misuse that repeats the same step every day alerts only on its first days, no worse than the "
                   "base formula, whose 90-day history also learns the habit within a few days.", {})],
         "size": 14}], anchor=MSO_ANCHOR.MIDDLE)


def s_learned(prs):
    s = new_slide(prs, "Title Only", "Two things learned on the way",
                  "The floor: in a quiet organisation the budget threshold drops to 1.3 bits, so a floor of 4 bits "
                  "stops the budget being spent on noise, and the crowd idea needs it. Persistence was tried and "
                  "dropped: it echoed alerts and cost 9 points. The graded crowd was close to the fold; the fold "
                  "is kept because it is simpler.")
    cw = (WIDTH - 0.3) / 2
    cards = [("A floor of 4 bits", "The budget is a ceiling, not a quota", "9 → 2",
              "organisation alerts in 3 days, control scenario",
              ["In a quiet organisation the budget threshold drops to 1.3 bits: ordinary noise.",
               "With the floor a day must be 16 times rarer than normal. Every real scenario is still flagged.",
               "The crowd idea needs it: without it the slowdown still leaves 38 alerts."]),
             ("Tried and dropped", "Persistence: yesterday's score fades into today", "50/58 → 41/52",
              "detection on the 9 organisations (≤ 2 / ≤ 4 a day)",
              ["It only echoed alerts into the next days: page walks −42, loops −25 points.",
               "Graded crowd, X ÷ (1 + c/3): close (3 and 1 alerts left, against 2 and 0). The fold is kept: "
               "simpler, and it gives one clear notice."])]
    for i, (head, sub, big, cap, items) in enumerate(cards):
        x = LEFT + i * (cw + 0.3)
        box(s, x, TOP, cw, 5.3)
        text(s, x + 0.3, TOP + 0.25, cw - 0.6, 0.9, [{"t": head, "size": 20, "bold": True, "color": NAVY, "after": 2},
                                                    {"t": sub, "size": 15, "italic": True, "color": GRAY}])
        text(s, x + 0.3, TOP + 1.25, cw - 0.6, 0.8, [{"t": big, "size": 40, "bold": True, "color": RED}],
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, x + 0.3, TOP + 2.05, cw - 0.6, 0.4, [{"t": cap, "size": 13, "color": MUTED}])
        text(s, x + 0.3, TOP + 2.7, cw - 0.6, 2.5, [{"t": t, "size": 14, "after": 10} for t in items])


def s_nine(prs):
    s = new_slide(prs, "Title Only", "On the 9 organisations the ideas cost almost nothing",
                  "Both ideas keep 50% / 58%. Their value does not show here: these organisations have no "
                  "organisation-wide changes and role changes fall on about 1% of alerts. Persistence costs 9 and "
                  "6 points. The floor sends 2.3 alerts a day instead of 4 at about the same detection per alert. "
                  "In the largest organisation (150 agents) the crowd raised 0.8 notices a day, so the 5-agent "
                  "threshold should grow with size.")
    cats = ["Base formula", "+ crowd", "+ settling", "+ both", "+ persistence (dropped)", "Base + floor of 4 bits"]
    bar_chart(s, LEFT - 0.1, TOP - 0.05, 7.6, 5.35, cats,
              {"≤ 2 flagged agent-days a day": [50, 50, 50, 50, 41, 49],
               "≤ 4 flagged agent-days a day": [58, 58, 58, 58, 52, 52]}, [NAVY, CORAL], label_size=12)
    box(s, 8.75, TOP, 3.75, 5.25, fill=CARD)
    text(s, 9.0, TOP + 0.25, 3.3, 4.9, [
        {"t": "Why the gain does not show here", "size": 17, "bold": True, "color": NAVY, "after": 8},
        {"t": "No organisation-wide changes; role changes fall on about 1% of alerts.", "size": 13,
         "after": 12},
        {"t": "The floor", "size": 15, "bold": True, "color": NAVY, "after": 4},
        {"t": "2.3 alerts a day instead of 4, about the same detection per alert.", "size": 13,
         "after": 12},
        {"t": "Notice volume", "size": 15, "bold": True, "color": NAVY, "after": 4},
        {"t": "0.8 a day in the 150-agent organisation, 0.1 or fewer elsewhere: the 5-agent threshold should "
              "grow with size.", "size": 13}])


def s_needs(prs):
    s = new_slide(prs, "Title Only", "What a deployment needs",
                  "gateway-log/2 already has every field except identity: add the OAuth sub, hashed, and the "
                  "client_id from the bearer token. State is about 70 KB per user plus agent app and shards by "
                  "agent; the organisation keeps one normal level per dimension.")
    rows = [["Log field", "Used for", "Status"],
            ["Timestamp", "Pace, the daily check", "have"],
            ["Tool name", "Pace, Path", "have"],
            ["Session id", "Path (what came before)", "have"],
            ["Client address, cut to /16", "Place", "have"],
            ["Client name, version dropped", "Place", "have"],
            ["User + agent app (OAuth sub, client_id)", "Whose history to compare with", "ADD"]]
    table(s, LEFT, TOP, [3.4, 2.6, 0.9], rows, size=12, row_h=0.5, fills={6: SOFT_RED})
    x = 8.05
    box(s, x, TOP, 4.45, 4.3)
    text(s, x + 0.3, TOP + 0.2, 3.9, 5.0, [
        {"t": "State", "size": 15, "bold": True, "color": NAVY, "after": 4},
        {"t": "About 70 KB per user + agent app, sharded by agent. Per organisation: the normal level B for "
              "each dimension.", "size": 13, "after": 12},
        {"t": "Parameters", "size": 15, "bold": True, "color": NAVY, "after": 4},
        {"t": "History 90 days · repeat window 10 min · team fill-in 20 calls · B = 99.5th percentile of 30 "
              "days · λ = ln 2 / 10 · cap ×8 · floor 4 bits · crowd 5 agents · settling 3 of 7 days",
         "size": 13, "after": 12},
        {"t": "From the policy (optional)", "size": 15, "bold": True, "color": NAVY, "after": 4},
        {"t": "Working hours (off-hours is invisible without them) and planned-change windows.", "size": 13}])
    text(s, LEFT, 5.15, 6.9, 1.5, [
        {"t": "Static scan: the static score per tool (R_static).", "size": 14, "after": 6},
        {"t": "Scale: a Python prototype ran 10,000 agents at about 21,000 calls a second on one core.",
         "size": 14, "color": GRAY}])


def s_keep(prs):
    s = new_slide(prs, "Title Only", "Keep in mind",
                  "Identity decides everything. The first month is calibration. Dynamic decides which agent-days "
                  "are strange; static decides which to look at first. The traffic is synthetic, so the next step "
                  "is real multi-agent gateway traffic.")
    items = [("Identity decides everything",
              "One token per person 75%; one token shared by 10 people 71% and you cannot tell who; session id "
              "only 12%."),
             ("The first month is calibration",
              "B needs 30 days of the organisation's traffic. New agents lean on their team until they have "
              "history."),
             ("Dynamic says \"strange\", static says \"how much it matters\"",
              "The daily check picks the agent-days; R_static decides which to look at first."),
             ("The traffic is synthetic",
              "The ranking held across 9 organisations, but these are not production rates. Next: record real "
              "gateway traffic with several agents, users and clients, and rerun.")]
    for i, (head, body) in enumerate(items):
        y = TOP + i * 1.32
        box(s, LEFT, y, WIDTH, 1.15, fill=CARD if i % 2 == 0 else CARD2)
        circle(s, LEFT + 0.3, y + 0.33, 0.5, i + 1)
        text(s, LEFT + 1.1, y + 0.1, WIDTH - 1.4, 0.45, [{"t": head, "size": 16, "bold": True}],
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, LEFT + 1.1, y + 0.55, WIDTH - 1.4, 0.55, [{"t": body, "size": 13, "color": GRAY}])


def s_close(prs):
    s = prs.slides.add_slide(layout(prs, "Closing Slide_Black"))
    s.notes_slide.notes_text_frame.text = "Questions. Files: FORMULA.md, SCENARIOS.md, dynamic_engine.py."


def main():
    prs = open_template()
    for build in (s_title, s_what, s_three, s_formula, s_example, s_why, s_kinds, s_sources, s_section,
                  s_setup, s_single, s_breaks, s_crowd, s_settle, s_learned, s_nine, s_needs, s_keep, s_close):
        build(prs)
    prs.save(str(OUT))
    print(f"wrote {OUT} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
