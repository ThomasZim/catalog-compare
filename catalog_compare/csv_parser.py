"""Parsing CSV intelligent avec gestion encoding, BOM, et séparateurs."""

from __future__ import annotations

import csv
import io


def detect_encoding(file_path: str) -> str:
    """Détecte l'encoding d'un fichier CSV."""
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read(4096)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return "latin-1"


def detect_delimiter(sample: str) -> str:
    """Détecte le délimiteur (virgule, point-virgule, tab)."""
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample, delimiters=",;\t")
        return dialect.delimiter
    except csv.Error:
        return ","


def _unwrap_quoted_rows(lines: list[str]) -> list[str]:
    """Corrige les CSV dont chaque ligne de données est enveloppée dans des guillemets.

    Certains exports (ex: Shopify) encapsulent chaque ligne dans "...",
    avec des guillemets internes doublés "". On retire l'enveloppe et
    on restaure les guillemets internes.
    """
    if len(lines) < 2:
        return lines

    # Vérifier si les lignes de données sont enveloppées
    test_line = lines[1].strip()
    if not (test_line.startswith('"') and test_line.endswith('"')):
        return lines

    # Tester : parser la ligne enveloppée donne-t-elle un seul champ ?
    parsed = list(csv.reader([lines[1].strip()]))[0]
    header_count = len(list(csv.reader([lines[0].strip()]))[0])
    if len(parsed) >= header_count // 2:
        return lines  # Pas enveloppé, le parsing normal fonctionne

    result = [lines[0]]
    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith('"') and stripped.endswith('"'):
            # Retirer les guillemets externes et restaurer les internes
            inner = stripped[1:-1].replace('""', '"')
            result.append(inner + "\n")
        else:
            result.append(line)

    return result


def parse_csv(file_path: str) -> tuple[list[str], list[list[str]]]:
    """Parse un fichier CSV et retourne (headers, rows).

    Gère : encoding varié, BOM, délimiteurs multiples, lignes enveloppées.
    """
    encoding = detect_encoding(file_path)

    with open(file_path, "r", encoding=encoding) as f:
        lines = f.readlines()

    if not lines:
        return [], []

    # Corriger les CSV avec lignes enveloppées dans des guillemets
    lines = _unwrap_quoted_rows(lines)

    delimiter = detect_delimiter(lines[0])

    reader = csv.reader(lines, delimiter=delimiter)
    rows = list(reader)

    if not rows:
        return [], []

    headers = [h.strip() for h in rows[0]]
    data = rows[1:]

    return headers, data


def auto_detect_columns(headers: list[str]) -> dict[str, int | None]:
    """Auto-détecte les colonnes barcode, cost, name.

    Retourne un dict avec les indices détectés (ou None).
    """
    result = {"barcode": None, "cost": None, "name": None}

    lower_headers = [h.lower().strip() for h in headers]

    for i, h in enumerate(lower_headers):
        if result["barcode"] is None and "barcode" in h:
            result["barcode"] = i

        if result["cost"] is None and ("cost" in h or "coût" in h or "cout" in h):
            result["cost"] = i

        if result["name"] is None:
            if any(kw in h for kw in ["title", "designation", "désignation", "nom", "name"]):
                result["name"] = i

    return result


def auto_detect_base_columns(headers: list[str]) -> dict[str, int | None]:
    """Auto-détecte les colonnes supplémentaires du CSV base (Shopify).

    Détecte : price (prix de vente), inventory_qty, continue_selling.
    """
    result = {"price": None, "inventory_qty": None, "continue_selling": None}

    lower_headers = [h.lower().strip() for h in headers]

    for i, h in enumerate(lower_headers):
        # Price : chercher "price"/"prix" en excluant "cost"/"cout"/"compare"
        if result["price"] is None and ("price" in h or "prix" in h):
            if not any(excl in h for excl in ["cost", "cout", "coût", "compare"]):
                result["price"] = i

        # Inventory qty : "inventory" + "qty"/"quantity", ou "stock"
        if result["inventory_qty"] is None:
            if ("inventory" in h and ("qty" in h or "quantity" in h)) or h == "stock":
                result["inventory_qty"] = i

        # Continue selling : "inventory policy" ou "continue selling"
        if result["continue_selling"] is None:
            if "inventory policy" in h or "continue selling" in h:
                result["continue_selling"] = i

    return result
