
from typing import List, Tuple
import math

# 🔗 Import YOUR carbon estimation engine
from .carbon_engine.pipeline import run_pipeline


class EnhancedFootprintMatcher:
    """
    Unified footprint matcher that delegates carbon estimation to:
    - Raw-material pipeline (manufactured / vague items)
    - Fixed factors (utility / transport)
    """

    # -------------------------------
    # Fixed emission factors
    # -------------------------------
    UTILITY_FACTORS = {
        "electricity_kwh": 0.4,
        "water_liter": 0.0003,
        "gas_therm": 5.3,
    }

    TRANSPORT_FACTORS = {
        "car_km": 0.17,
        "bus_km": 0.08,
        "train_km": 0.04,
        "flight_km": 0.25,
        "fuel_liter": 2.3,
    }

    SIMPLE_CATEGORIES = {"utility", "transport"}

    # -------------------------------
    # Public API
    # -------------------------------
    def match_and_compute(self, items: List[dict]) -> Tuple[List[dict], float]:
        """
        Main entry used by CarbonDrop.
        Input & output format remains unchanged.
        """
        results = []
        total = 0.0

        for it in items:
            name = it.get("name", "").strip()
            qty = float(it.get("qty", 1) or 1)
            unit = it.get("unit", "")
            category = (it.get("category") or "unknown").lower()

            # Decide estimation strategy
            if category in self.SIMPLE_CATEGORIES:
                footprint = self._compute_simple(category, qty, unit, name)
                result = self._format_result(
                    name=name,
                    matched_name="simple_factor",
                    match_score=90,
                    qty=qty,
                    unit=unit,
                    footprint=footprint,
                    category=category
                )

            else:
                # 🚀 USE YOUR PIPELINE
                footprint, confidence = self._compute_via_pipeline(name)

                result = self._format_result(
                    name=name,
                    matched_name="estimated_via_pipeline",
                    match_score=int(confidence * 100),
                    qty=qty,
                    unit=unit,
                    footprint=footprint,
                    category=category
                )

            results.append(result)
            total += footprint

        return results, round(total, 4)

    # -------------------------------
    # Pipeline-based estimation
    # -------------------------------
    def _compute_via_pipeline(self, product_name: str) -> Tuple[float, float]:
        """
        Delegates carbon estimation to the raw-material pipeline.
        """
        try:
            pipeline_result = run_pipeline(
                product_name=product_name,
                weight="NA",
                energy_kwh=0,
                region="India"
            )

            return (
                float(pipeline_result["total_emission"]),
                float(pipeline_result["confidence"])
            )

        except Exception as e:
            print(f"[Pipeline Error] {product_name}: {e}")
            return 0.0, 0.0

    # -------------------------------
    # Simple factor-based estimation
    # -------------------------------
    def _compute_simple(self, category: str, qty: float, unit: str, name: str) -> float:
        """
        Utility / transport estimation using fixed factors.
        """
        key = f"{name.lower()}_{unit}".replace(" ", "_")

        if category == "utility":
            factor = self.UTILITY_FACTORS.get(key) or self.UTILITY_FACTORS.get(unit, 0)
            return round(qty * factor, 4)

        if category == "transport":
            factor = self.TRANSPORT_FACTORS.get(key) or self.TRANSPORT_FACTORS.get(unit, 0)
            return round(qty * factor, 4)

        return 0.0

    # -------------------------------
    # Result formatter
    # -------------------------------
    def _format_result(
        self,
        name: str,
        matched_name: str,
        match_score: int,
        qty: float,
        unit: str,
        footprint: float,
        category: str
    ) -> dict:
        """
        Ensures CarbonDrop-compatible output.
        """
        return {
            "name": name,
            "matched_name": matched_name,
            "match_score": match_score,
            "qty": qty,
            "unit": unit,
            "co2_per_unit": (
                round(footprint / qty, 4) if qty > 0 else 0
            ),
            "footprint": round(footprint, 4),
            "category": category,
        }
