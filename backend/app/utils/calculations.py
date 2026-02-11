"""
Energy-savings calculation helpers.

All constants are based on the French electricity grid and regulated
residential tariffs (EDF Tarif Bleu, 2024 schedule).

References
----------
- CO2 factor: ADEME Base Carbone -- France mainland electricity mix
  ~0.0569 kg CO2 / kWh.
- Tariffs: CRE published rates for residential consumers.
- Heating rule of thumb: 1 degree Celsius reduction in thermostat
  setpoint yields roughly 7 % savings on heating consumption.
"""

from __future__ import annotations

# ── Constants ─────────────────────────────────────────────────────────────

# kg CO2 emitted per kWh of French grid electricity
CO2_FACTOR_KG_PER_KWH: float = 0.0569

# Electricity tariffs (EUR / kWh)
TARIFF_RATES: dict[str, float] = {
    "base": 0.2016,
    "peak": 0.2700,
    "off_peak": 0.1470,
}

# Average residential heating power density (W / m2)
AVERAGE_HEATING_W_PER_M2: float = 50.0

# Fraction of heating energy saved per 1 degree C reduction
HEATING_SAVINGS_PER_DEGREE: float = 0.07


# ── Public helpers ────────────────────────────────────────────────────────


def calculate_co2_savings(kwh_saved: float) -> float:
    """Return the CO2 savings in **kilograms** for a given energy reduction.

    Parameters
    ----------
    kwh_saved:
        Electrical energy saved, in kWh.  Must be non-negative.

    Returns
    -------
    float
        CO2 not emitted, in kg.
    """
    if kwh_saved < 0:
        raise ValueError("kwh_saved must be non-negative")
    return round(kwh_saved * CO2_FACTOR_KG_PER_KWH, 4)


def calculate_cost_savings(
    kwh_saved: float,
    tariff: str = "base",
) -> float:
    """Return the monetary savings in **euros** for a given energy reduction.

    Parameters
    ----------
    kwh_saved:
        Electrical energy saved, in kWh.  Must be non-negative.
    tariff:
        One of ``"base"``, ``"peak"``, or ``"off_peak"``.

    Returns
    -------
    float
        Amount saved, in EUR.

    Raises
    ------
    ValueError
        If *tariff* is not a recognised key or *kwh_saved* is negative.
    """
    if kwh_saved < 0:
        raise ValueError("kwh_saved must be non-negative")

    rate = TARIFF_RATES.get(tariff)
    if rate is None:
        valid = ", ".join(sorted(TARIFF_RATES))
        raise ValueError(f"Unknown tariff '{tariff}'. Valid options: {valid}")

    return round(kwh_saved * rate, 4)


def calculate_heating_savings(
    temp_reduction: float,
    duration_hours: float,
    surface_m2: float,
) -> dict[str, float]:
    """Estimate heating savings from lowering the thermostat setpoint.

    Parameters
    ----------
    temp_reduction:
        How many degrees Celsius the setpoint is lowered (must be > 0).
    duration_hours:
        Duration over which the reduction is applied, in hours.
    surface_m2:
        Heated surface area, in square metres.

    Returns
    -------
    dict
        ``{"kwh_saved": …, "eur_saved": …, "co2_saved": …}``
        where *eur_saved* uses the base tariff and *co2_saved* is in kg.

    Raises
    ------
    ValueError
        If any parameter is non-positive.
    """
    if temp_reduction <= 0:
        raise ValueError("temp_reduction must be positive")
    if duration_hours <= 0:
        raise ValueError("duration_hours must be positive")
    if surface_m2 <= 0:
        raise ValueError("surface_m2 must be positive")

    # Baseline heating consumption over the period (kWh)
    baseline_kwh = (AVERAGE_HEATING_W_PER_M2 * surface_m2 * duration_hours) / 1000.0

    # Savings fraction (capped at 100 %)
    savings_fraction = min(temp_reduction * HEATING_SAVINGS_PER_DEGREE, 1.0)

    kwh_saved = round(baseline_kwh * savings_fraction, 4)
    eur_saved = calculate_cost_savings(kwh_saved, tariff="base")
    co2_saved = calculate_co2_savings(kwh_saved)

    return {
        "kwh_saved": kwh_saved,
        "eur_saved": eur_saved,
        "co2_saved": co2_saved,
    }
