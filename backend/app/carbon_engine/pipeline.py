import json

from estimators.product_classifier import classify_product
from estimators.material_estimator import estimate_materials
from estimators.process_estimator import estimate_processes

from calculator.material_emission import calculate_material_emission
from calculator.process_emission import calculate_process_emission
from calculator.energy_emission import calculate_energy_emission
from calculator.total_emission import calculate_total


# -------------------------------
# Utility: Safe input handler
# -------------------------------
def get_input(prompt, cast_type=float, allow_na=True, default=0):
    value = input(prompt).strip()

    if allow_na and value.upper() == "NA":
        return default

    try:
        return cast_type(value)
    except ValueError:
        print(f"Invalid input. Using default value: {default}")
        return default


# -------------------------------
# Clarification logic for vague products
# -------------------------------
def clarify_product(product_name, product_type, confidence):
    print("\nAdditional details needed to identify the product.")

    details = {}

    # Apparel clarification
    if product_type == "apparel":
        details["gender"] = input(
            "Is it for Men or Women? "
        ).strip().lower()

        details["fabric"] = input(
            "Primary fabric (cotton / denim / polyester)? "
        ).strip().lower()

    # Metal fabrication clarification
    elif product_type == "metal_fabrication":
        details["usage"] = input(
            "Is it Indoor or Outdoor? "
        ).strip().lower()

        details["thickness"] = input(
            "Approx thickness (thin / medium / thick)? "
        ).strip().lower()

    # Unknown product
    else:
        details["material"] = input(
            "Main material (steel / plastic / fabric / wood)? "
        ).strip().lower()

        details["purpose"] = input(
            "Purpose (wearable / construction / furniture)? "
        ).strip().lower()

    return details


# -------------------------------
# Core pipeline
# -------------------------------
def run_pipeline(product_name, weight, energy_kwh, region="India"):
    product_type, confidence = classify_product(product_name)

    details = {}
    if confidence < 0.8:
        details = clarify_product(product_name, product_type, confidence)

    # Load datasets
    with open("data/raw.json") as f:
        raw_factors = json.load(f)

    with open("data/process.json") as f:
        process_factors = json.load(f)

    with open("data/region_energy.json") as f:
        energy_factors = json.load(f)

    # Estimate materials & processes
    materials = estimate_materials(product_type, weight, details)
    processes = estimate_processes(product_type)

    # Calculate emissions
    material_emission = calculate_material_emission(
        materials, raw_factors
    )

    process_emission = calculate_process_emission(
        processes, weight, process_factors
    )

    energy_emission = calculate_energy_emission(
        energy_kwh, energy_factors.get(region, {}).get("electricity", 0)
    )

    total_emission = calculate_total(
        material_emission,
        process_emission,
        energy_emission
    )

    return {
        "product": product_name,
        "category": product_type,
        "confidence": confidence,
        "materials": materials,
        "material_emission": round(material_emission, 2),
        "process_emission": round(process_emission, 2),
        "energy_emission": round(energy_emission, 2),
        "total_emission": round(total_emission, 2),
    }


# -------------------------------
# INTERACTIVE TERMINAL ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    print("\n===================================")
    print("  CARBON EMISSION ESTIMATION TOOL  ")
    print("===================================\n")

    product_name = input("Enter product name: ").strip()

    weight = get_input(
        "Enter product weight in kg (NA if unknown): ",
        float,
        allow_na=True,
        default=10
    )

    energy_kwh = get_input(
        "Enter electricity used in kWh (NA if unknown): ",
        float,
        allow_na=True,
        default=0
    )

    region = input(
        "Enter region (default: India): "
    ).strip() or "India"

    result = run_pipeline(
        product_name=product_name,
        weight=weight,
        energy_kwh=energy_kwh,
        region=region
    )

    output = {
        "product": result["product"],
        "category": result["category"],
        "confidence": round(result["confidence"], 2),
        "inputs": {
            "weight_kg": weight,
            "energy_kwh": energy_kwh,
            "region": region
        },
        "materials": result["materials"],
        "emissions_kg_co2": {
            "material": result["material_emission"],
            "process": result["process_emission"],
            "energy": result["energy_emission"],
            "total": result["total_emission"]
        }
    }

    print("\n===== JSON OUTPUT =====")
    print(json.dumps(output, indent=4))