import pytest

from devops_lab.shipping_service import calculate_shipping


def test_calculate_shipping_accepts_numeric_tax_rate() -> None:
    assert calculate_shipping(100.0, "12.5") == 112.5

# Test for calculate_shipping with numeric tax rate