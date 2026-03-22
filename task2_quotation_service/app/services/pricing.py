"""
Pricing engine for the Quotation Microservice.
Loads product catalogue from JSON (or uses in-memory mock).
Applies quantity-based tiered pricing and discount logic.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Built-in mock catalogue (used when price_list.json is absent / MOCK_MODE) ─

MOCK_CATALOGUE: Dict[str, dict] = {
    "LED-PANEL-60W": {
        "name": "LED Panel Light 60W",
        "base_price": 14.00,
        "min_qty": 1,
        "tiers": [
            {"min_qty": 100, "unit_price": 13.00},
            {"min_qty": 500, "unit_price": 12.00},
            {"min_qty": 1000, "unit_price": 10.50},
        ],
    },
    "LED-STREET-100W": {
        "name": "LED Street Light 100W",
        "base_price": 45.00,
        "min_qty": 1,
        "tiers": [
            {"min_qty": 50, "unit_price": 42.00},
            {"min_qty": 200, "unit_price": 38.00},
            {"min_qty": 500, "unit_price": 34.00},
        ],
    },
    "LED-HIGHBAY-150W": {
        "name": "LED High Bay Light 150W",
        "base_price": 55.00,
        "min_qty": 1,
        "tiers": [
            {"min_qty": 50, "unit_price": 52.00},
            {"min_qty": 200, "unit_price": 47.00},
            {"min_qty": 500, "unit_price": 42.00},
        ],
    },
    "LED-DOWNLIGHT-12W": {
        "name": "LED Downlight 12W",
        "base_price": 5.50,
        "min_qty": 1,
        "tiers": [
            {"min_qty": 500, "unit_price": 4.80},
            {"min_qty": 2000, "unit_price": 4.20},
            {"min_qty": 5000, "unit_price": 3.80},
        ],
    },
    "LED-TUBE-18W": {
        "name": "LED Tube Light T8 18W",
        "base_price": 4.00,
        "min_qty": 1,
        "tiers": [
            {"min_qty": 500, "unit_price": 3.50},
            {"min_qty": 2000, "unit_price": 3.10},
            {"min_qty": 5000, "unit_price": 2.80},
        ],
    },
}


class PricingEngine:
    """
    Resolves unit prices from the product catalogue with tiered logic.
    Falls back gracefully to mock data if catalogue file is missing.
    """

    def __init__(self, price_list_path: str = "./data/price_list.json"):
        self._catalogue: Dict[str, dict] = {}
        self._load_catalogue(price_list_path)

    def _load_catalogue(self, path: str) -> None:
        p = Path(path)
        if p.exists():
            try:
                with open(p) as f:
                    self._catalogue = json.load(f)
                logger.info("Loaded product catalogue from %s (%d SKUs)", path, len(self._catalogue))
                return
            except Exception as exc:
                logger.warning("Failed to load price list from %s: %s – using mock catalogue", path, exc)
        else:
            logger.info("Price list not found at %s – using built-in mock catalogue", path)
        self._catalogue = MOCK_CATALOGUE

    def resolve(self, sku: str, quantity: int, override_price: Optional[float] = None) -> Tuple[str, float, float]:
        """
        Returns (product_name, unit_price, discount_pct).
        Raises ValueError if SKU is unknown.
        """
        if sku not in self._catalogue:
            raise ValueError(f"Unknown product SKU: {sku!r}")

        product = self._catalogue[sku]
        product_name: str = product["name"]

        if override_price is not None:
            return product_name, float(override_price), 0.0

        # Tiered pricing: find highest tier where quantity >= min_qty
        unit_price: float = float(product["base_price"])
        for tier in sorted(product.get("tiers", []), key=lambda t: t["min_qty"]):
            if quantity >= tier["min_qty"]:
                unit_price = float(tier["unit_price"])

        # Volume discount on top of tiered price
        discount_pct = self._volume_discount(quantity)
        return product_name, unit_price, discount_pct

    @staticmethod
    def _volume_discount(qty: int) -> float:
        """Returns extra discount percentage based on order volume."""
        if qty >= 10_000:
            return 5.0
        if qty >= 5_000:
            return 3.0
        if qty >= 1_000:
            return 1.5
        return 0.0

    def known_skus(self) -> list[str]:
        return list(self._catalogue.keys())
