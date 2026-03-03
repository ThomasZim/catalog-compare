"""Logique de comparaison de deux catalogues par barcode."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .cost_parser import parse_cost


def normalize_barcode(raw: str) -> str:
    """Ne garde que les chiffres d'un barcode (supprime espaces, apostrophes, etc.)."""
    return re.sub(r"\D", "", raw)


@dataclass
class Product:
    barcode: str
    name: str
    cost: float | None
    raw_cost: str


@dataclass
class CostChange:
    barcode: str
    old_name: str
    new_name: str
    name_changed: bool
    old_cost: float | None
    new_cost: float | None
    old_raw: str
    new_raw: str
    variation_pct: float | None


@dataclass
class ComparisonResult:
    old_count: int
    new_count: int
    appeared: list[Product]
    disappeared: list[Product]
    cost_changes: list[CostChange]


def build_index(
    rows: list[list[str]],
    barcode_col: int,
    cost_col: int,
    name_col: int,
) -> dict[str, Product]:
    """Indexe les produits par barcode. Ignore les barcodes vides."""
    index: dict[str, Product] = {}

    for row in rows:
        if barcode_col >= len(row) or name_col >= len(row):
            continue

        barcode = normalize_barcode(row[barcode_col])
        if not barcode:
            continue

        raw_cost = row[cost_col].strip() if cost_col < len(row) else ""
        name = row[name_col].strip()

        index[barcode] = Product(
            barcode=barcode,
            name=name,
            cost=parse_cost(raw_cost),
            raw_cost=raw_cost,
        )

    return index


def compare_catalogs(
    old_rows: list[list[str]],
    old_cols: dict[str, int],
    new_rows: list[list[str]],
    new_cols: dict[str, int],
) -> ComparisonResult:
    """Compare deux catalogues et retourne les différences."""
    old_index = build_index(
        old_rows, old_cols["barcode"], old_cols["cost"], old_cols["name"]
    )
    new_index = build_index(
        new_rows, new_cols["barcode"], new_cols["cost"], new_cols["name"]
    )

    old_barcodes = set(old_index.keys())
    new_barcodes = set(new_index.keys())

    # Produits apparus
    appeared = [
        new_index[bc]
        for bc in sorted(new_barcodes - old_barcodes)
    ]

    # Produits disparus
    disappeared = [
        old_index[bc]
        for bc in sorted(old_barcodes - new_barcodes)
    ]

    # Changements de cout ou de nom
    cost_changes: list[CostChange] = []
    for bc in sorted(old_barcodes & new_barcodes):
        old_p = old_index[bc]
        new_p = new_index[bc]

        cost_changed = old_p.cost != new_p.cost
        old_norm = old_p.name.lower().replace("*", "").replace(" ", "")
        new_norm = new_p.name.lower().replace("*", "").replace(" ", "")
        name_changed = old_norm != new_norm

        if not cost_changed and not name_changed:
            continue

        variation = None
        if old_p.cost is not None and new_p.cost is not None and old_p.cost != 0:
            variation = round(((new_p.cost - old_p.cost) / old_p.cost) * 100, 1)

        cost_changes.append(CostChange(
            barcode=bc,
            old_name=old_p.name,
            new_name=new_p.name,
            name_changed=name_changed,
            old_cost=old_p.cost,
            new_cost=new_p.cost,
            old_raw=old_p.raw_cost,
            new_raw=new_p.raw_cost,
            variation_pct=variation,
        ))

    return ComparisonResult(
        old_count=len(old_index),
        new_count=len(new_index),
        appeared=appeared,
        disappeared=disappeared,
        cost_changes=cost_changes,
    )
