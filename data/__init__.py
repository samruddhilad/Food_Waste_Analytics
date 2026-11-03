"""
Data processing and integration module for Food Waste Management Dashboard.
"""
from .processing import (
    load_food_listings,
    load_providers,
    load_receivers,
    load_claims,
    create_integrated_dataset,
    clean_and_enrich_data,
    get_dataset_summary
)

__all__ = [
    "load_food_listings",
    "load_providers",
    "load_receivers",
    "load_claims",
    "create_integrated_dataset",
    "clean_and_enrich_data",
    "get_dataset_summary"
]
