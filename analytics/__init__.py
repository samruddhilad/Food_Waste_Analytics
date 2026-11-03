"""
Analytics module for Food Waste Management Dashboard.
"""
from .analytics import (
    compute_kpi_metrics,
    get_food_type_distribution,
    get_meal_type_distribution,
    get_city_food_distribution,
    get_expiry_trend,
    get_top_providers,
    get_provider_type_distribution,
    get_top_receivers,
    get_receiver_type_distribution,
    get_claim_status_distribution,
    get_waste_indicators,
    get_redistribution_recommendations
)

__all__ = [
    "compute_kpi_metrics",
    "get_food_type_distribution",
    "get_meal_type_distribution",
    "get_city_food_distribution",
    "get_expiry_trend",
    "get_top_providers",
    "get_provider_type_distribution",
    "get_top_receivers",
    "get_receiver_type_distribution",
    "get_claim_status_distribution",
    "get_waste_indicators",
    "get_redistribution_recommendations"
]
