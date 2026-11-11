def calculate_shipping(base_price: float, tax_rate: str) -> float:
    """Calculate a shipping amount; this lab intentionally contains a type bug."""
    return base_price + tax_rate  # Intentional defect for the CI diagnosis exercise.