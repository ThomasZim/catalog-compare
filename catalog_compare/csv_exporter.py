"""Export d'un CSV base modifié avec prix mis à jour et produits obsolètes désactivés."""

from __future__ import annotations

import csv

from .comparator import ComparisonResult
from .csv_parser import detect_delimiter, detect_encoding


def export_modified_csv(
    base_path: str,
    output_path: str,
    base_rows: list[list[str]],
    base_headers: list[str],
    cols: dict[str, int],
    comparison_result: ComparisonResult,
    multiplier: float,
) -> None:
    """Exporte un CSV base modifié.

    - Met à jour le cost et le price pour les produits avec changement de coût
    - Désactive les produits disparus (inventory qty = 0, continue selling = deny)
    - Préserve l'encoding et le delimiter de l'original
    """
    encoding = detect_encoding(base_path)

    with open(base_path, "r", encoding=encoding) as f:
        sample = f.readline()
    delimiter = detect_delimiter(sample)

    barcode_col = cols["barcode"]
    cost_col = cols["cost"]
    price_col = cols["price"]
    inv_qty_col = cols["inventory_qty"]
    continue_selling_col = cols["continue_selling"]

    # Set des barcodes du nouveau CSV (présents dans le nouveau catalogue)
    new_barcodes: set[str] = set()
    for p in comparison_result.appeared:
        new_barcodes.add(p.barcode)
    for c in comparison_result.cost_changes:
        new_barcodes.add(c.barcode)
    # Ajouter les barcodes communs sans changement (old & new moins disappeared)
    disappeared_barcodes = {p.barcode for p in comparison_result.disappeared}

    # Dict barcode -> new_cost depuis les cost_changes
    cost_updates: dict[str, float] = {}
    for c in comparison_result.cost_changes:
        if c.new_cost is not None:
            cost_updates[c.barcode] = c.new_cost

    # Construire les lignes modifiées
    output_rows: list[list[str]] = []
    for row in base_rows:
        new_row = list(row)

        if barcode_col >= len(row):
            output_rows.append(new_row)
            continue

        barcode = row[barcode_col].strip()
        if not barcode:
            output_rows.append(new_row)
            continue

        # Produit avec changement de coût
        if barcode in cost_updates:
            new_cost = cost_updates[barcode]
            if cost_col < len(new_row):
                new_row[cost_col] = f"{new_cost:.2f}"
            if price_col < len(new_row):
                new_row[price_col] = f"{new_cost * multiplier:.2f}"

        # Produit disparu (dans base mais pas dans nouveau)
        if barcode in disappeared_barcodes:
            if inv_qty_col < len(new_row):
                new_row[inv_qty_col] = "0"
            if continue_selling_col < len(new_row):
                new_row[continue_selling_col] = "deny"

        output_rows.append(new_row)

    # Écrire le CSV avec le même encoding et delimiter
    with open(output_path, "w", encoding=encoding, newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(base_headers)
        writer.writerows(output_rows)
