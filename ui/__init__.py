"""
UI components and dashboard layout module for Food Waste Management Dashboard.
"""
from .styles import inject_custom_css, render_kpi_card, render_badge
from .charts import (
    plot_food_trend,
    plot_food_types_pie,
    plot_meal_types_bar,
    plot_city_availability_bar,
    plot_claim_status_donut,
    plot_top_providers_bar,
    plot_top_receivers_bar,
    plot_provider_types_pie,
    plot_receiver_types_pie,
    plot_geographic_map
)
from .dashboard import render_dashboard

__all__ = [
    "inject_custom_css",
    "render_kpi_card",
    "render_badge",
    "plot_food_trend",
    "plot_food_types_pie",
    "plot_meal_types_bar",
    "plot_city_availability_bar",
    "plot_claim_status_donut",
    "plot_top_providers_bar",
    "plot_top_receivers_bar",
    "plot_provider_types_pie",
    "plot_receiver_types_pie",
    "plot_geographic_map",
    "render_dashboard"
]
