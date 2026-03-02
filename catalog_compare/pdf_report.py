"""PDF report generation with fpdf2."""

from __future__ import annotations

import re
from datetime import datetime

from fpdf import FPDF

from .comparator import ComparisonResult


def _sanitize(text: str) -> str:
    """Replace non-Latin-1 characters to avoid Helvetica encoding errors."""
    replacements = {
        "\u2022": "-",   # bullet
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u00b7": "-",   # middle dot
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class CatalogReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "CATALOG COMPARISON", align="C", new_x="LMARGIN", new_y="NEXT")

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def _fmt_cost(cost: float | None) -> str:
    if cost is None:
        return "N/A"
    return f"{cost:.2f} EUR"


def _fmt_variation(pct: float | None) -> str:
    if pct is None:
        return "N/A"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.1f}%"


def _draw_table_header(pdf: FPDF, cols: list[tuple[str, int]]):
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(60, 60, 80)
    pdf.set_text_color(255, 255, 255)
    for label, width in cols:
        pdf.cell(width, 7, label, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_text_color(0, 0, 0)


def _draw_row(pdf: FPDF, cols: list[tuple[str, int]], values: list[str], fill: bool, align_list: list[str] | None = None):
    pdf.set_font("Helvetica", "", 7)
    if fill:
        pdf.set_fill_color(235, 235, 245)
    else:
        pdf.set_fill_color(255, 255, 255)

    if align_list is None:
        align_list = ["L"] * len(values)

    for i, (val, (_, width)) in enumerate(zip(values, cols)):
        pdf.cell(width, 6, _sanitize(val[:50]), border=1, fill=True, align=align_list[i])
    pdf.ln()


def generate_pdf(result: ComparisonResult, output_path: str):
    """Generate the catalog comparison PDF report."""
    pdf = CatalogReport(orientation="L")
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Metadata
    pdf.set_font("Helvetica", "", 9)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(0, 6, f"Date: {now}  |  Base: {result.old_count} products  |  New: {result.new_count} products",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Summary
    pdf.set_font("Helvetica", "B", 10)
    summary = (
        f"SUMMARY: {len(result.appeared)} added, "
        f"{len(result.disappeared)} removed, "
        f"{len(result.cost_changes)} changes"
    )
    pdf.cell(0, 8, summary, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    # 1. Added products
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 8, f"1. ADDED PRODUCTS ({len(result.appeared)})", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    if result.appeared:
        cols_app = [("Index", 50), ("Name", page_width - 85), ("Cost", 35)]
        _draw_table_header(pdf, cols_app)
        for i, p in enumerate(result.appeared):
            _draw_row(pdf, cols_app, [p.barcode, p.name, _fmt_cost(p.cost)], fill=(i % 2 == 0), align_list=["L", "L", "R"])
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "No added products.", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # 2. Removed products
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(0, 8, f"2. REMOVED PRODUCTS ({len(result.disappeared)})", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    if result.disappeared:
        cols_dis = [("Index", 50), ("Name", page_width - 85), ("Cost", 35)]
        _draw_table_header(pdf, cols_dis)
        for i, p in enumerate(result.disappeared):
            _draw_row(pdf, cols_dis, [p.barcode, p.name, _fmt_cost(p.cost)], fill=(i % 2 == 0), align_list=["L", "L", "R"])
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "No removed products.", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # 3. Changes
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 180)
    pdf.cell(0, 8, f"3. CHANGES ({len(result.cost_changes)})", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    if result.cost_changes:
        col_w = page_width
        name_w = int((col_w - 120) / 2)
        cols_chg = [
            ("Index", 35),
            ("Base name", name_w),
            ("New name", name_w),
            ("Base", 30),
            ("New", 30),
            ("Change", 25),
        ]
        _draw_table_header(pdf, cols_chg)

        for i, c in enumerate(result.cost_changes):
            variation_str = _fmt_variation(c.variation_pct)
            new_name_display = c.new_name if c.name_changed else "-"

            _draw_row(
                pdf, cols_chg,
                [c.barcode, c.old_name, new_name_display, _fmt_cost(c.old_cost), _fmt_cost(c.new_cost), variation_str],
                fill=(i % 2 == 0),
                align_list=["L", "L", "L", "R", "R", "R"],
            )
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "No changes.", new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_path)
