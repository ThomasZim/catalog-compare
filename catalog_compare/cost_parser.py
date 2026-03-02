"""Normalisation des montants depuis des formats hétérogènes."""

from __future__ import annotations

import re


def parse_cost(raw: str) -> float | None:
    """Parse un montant depuis des formats variés.

    Formats gérés :
    - "8,70 €"
    - "6,6"
    - "9"
    - "12.50"
    - vide / None
    """
    if raw is None:
        return None

    cleaned = raw.strip()
    if not cleaned:
        return None

    # Retirer tout sauf chiffres, virgule, point
    cleaned = re.sub(r"[^\d,.]", "", cleaned)

    if not cleaned:
        return None

    # Remplacer virgule par point (format FR -> float)
    cleaned = cleaned.replace(",", ".")

    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None
