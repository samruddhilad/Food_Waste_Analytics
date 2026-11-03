from typing import Dict, Any, List
import pandas as pd
from langchain_core.tools import tool
from data.processing import create_integrated_dataset
from analytics.analytics import (
    compute_kpi_metrics,
    get_food_type_distribution,
    get_top_providers,
    get_top_receivers,
    get_city_food_distribution,
    get_waste_indicators,
    get_redistribution_recommendations
)

# Cache loaded integrated dataset for tools
_cached_df = None

def _get_dataset() -> pd.DataFrame:
    global _cached_df
    if _cached_df is None:
        _cached_df = create_integrated_dataset()
    return _cached_df

def refresh_tool_dataset(df: pd.DataFrame = None):
    global _cached_df
    if df is not None:
        _cached_df = df
    else:
        _cached_df = create_integrated_dataset()

@tool
def get_food_statistics(query: str = "") -> Dict[str, Any]:
    """
    Returns overall statistics on food listings, total quantity, dietary categories, and meal distributions.
    Useful for questions like 'How much food is available?' or 'What are the food categories?'.
    """
    df = _get_dataset()
    kpis = compute_kpi_metrics(df)
    food_types = get_food_type_distribution(df).to_dict(orient="records")
    return {
        "total_food_listings": kpis["total_listings"],
        "total_food_quantity": kpis["total_quantity"],
        "unclaimed_quantity": kpis["unclaimed_quantity"],
        "critical_expiry_quantity": kpis["critical_quantity"],
        "food_dietary_types": food_types,
        "potential_meals": kpis["estimated_meals_potential"]
    }

@tool
def get_unclaimed_food(query: str = "") -> Dict[str, Any]:
    """
    Returns data about surplus food listings that remain unclaimed or unfulfilled.
    Useful for questions like 'Which food items are unclaimed?' or 'What is our unclaimed food rate?'.
    """
    df = _get_dataset()
    unclaimed = df[df["Claim_Status_Clean"] == "Unclaimed"].drop_duplicates(subset=["Food_ID"])
    total_unclaimed_qty = int(unclaimed["Quantity"].sum())
    top_unclaimed_cities = unclaimed.groupby("City")["Quantity"].sum().sort_values(ascending=False).head(5).to_dict()
    sample_items = unclaimed[["Food_ID", "Food_Name", "Quantity", "City", "Shelf_Life_Status"]].head(8).to_dict(orient="records")
    
    return {
        "unclaimed_listings_count": len(unclaimed),
        "total_unclaimed_quantity": total_unclaimed_qty,
        "top_cities_with_unclaimed_food": top_unclaimed_cities,
        "sample_unclaimed_items": sample_items
    }

@tool
def get_expiring_food(query: str = "") -> Dict[str, Any]:
    """
    Returns food items that are expiring soon (within 48 hours or approaching expiry) or already expired.
    Useful for questions like 'Which food items are expiring soon?' or 'What food should we prioritize before it goes bad?'.
    """
    df = _get_dataset()
    unique_food = df.drop_duplicates(subset=["Food_ID"])
    critical = unique_food[unique_food["Shelf_Life_Status"] == "Critical (<48h)"]
    approaching = unique_food[unique_food["Shelf_Life_Status"] == "Approaching Expiry (3-7d)"]
    expired = unique_food[unique_food["Shelf_Life_Status"] == "Expired"]
    
    urgent_items = critical[["Food_ID", "Food_Name", "Quantity", "Location", "Provider_Name", "Days_To_Expiry"]].head(10).to_dict(orient="records")
    
    return {
        "critical_expiring_count": len(critical),
        "critical_expiring_quantity": int(critical["Quantity"].sum()),
        "approaching_expiry_count": len(approaching),
        "approaching_expiry_quantity": int(approaching["Quantity"].sum()),
        "expired_items_count": len(expired),
        "urgent_critical_items": urgent_items
    }

@tool
def get_provider_statistics(query: str = "") -> Dict[str, Any]:
    """
    Returns data on top contributing food providers, provider types, and donation leaders.
    Useful for questions like 'Who are the top food providers?' or 'Which provider contributes the most?'.
    """
    df = _get_dataset()
    top_p = get_top_providers(df, top_n=8)
    return {
        "total_registered_providers": int(df["Provider_ID"].dropna().nunique()),
        "top_providers": top_p[["Provider_ID", "Provider_Name", "Provider_Business_Type", "City", "Total_Donated_Qty", "Completed_Claims"]].to_dict(orient="records")
    }

@tool
def get_receiver_statistics(query: str = "") -> Dict[str, Any]:
    """
    Returns data on registered receivers, top claimants (NGOs, Shelters, Charities), and claim activity.
    Useful for questions like 'Which receivers claim the most food?' or 'Who are the most active NGOs?'.
    """
    df = _get_dataset()
    top_r = get_top_receivers(df, top_n=8)
    return {
        "total_registered_receivers": int(df["Receiver_ID"].dropna().nunique()),
        "top_receivers": top_r[["Receiver_ID", "Receiver_Name", "Receiver_Organization_Type", "Receiver_City", "Total_Claims", "Completed_Claims", "Total_Quantity_Claimed"]].to_dict(orient="records")
    }

@tool
def get_claims_statistics(query: str = "") -> Dict[str, Any]:
    """
    Returns overall claim statistics, completion rates, pending claims, and cancellations.
    Useful for questions like 'How many claims were completed?' or 'What is the claim success rate?'.
    """
    df = _get_dataset()
    kpis = compute_kpi_metrics(df)
    return {
        "total_claims": kpis["total_claims"],
        "completed_claims": kpis["completed_claims"],
        "pending_claims": kpis["pending_claims"],
        "cancelled_claims": kpis["cancelled_claims"],
        "claim_fulfillment_rate_pct": kpis["claim_rate_pct"],
        "unclaimed_rate_pct": kpis["unclaimed_rate_pct"]
    }

@tool
def get_city_food_waste_summary(query: str = "") -> Dict[str, Any]:
    """
    Returns geographic food availability and unclaimed waste by city.
    Useful for questions like 'Which city has the highest food waste?' or 'Show food distribution by city'.
    """
    df = _get_dataset()
    city_dist = get_city_food_distribution(df)
    return {
        "top_cities_by_food_volume": city_dist.head(8).to_dict(orient="records"),
        "top_city_highest_waste": city_dist.sort_values(by="Unclaimed_Quantity", ascending=False).iloc[0].to_dict() if not city_dist.empty else {}
    }

@tool
def get_redistribution_candidates(query: str = "") -> Dict[str, Any]:
    """
    Generates actionable AI redistribution recommendations matching urgent surplus food to local receivers.
    Useful for questions like 'Which food should be prioritized for redistribution?' or 'Give me a redistribution recommendation'.
    """
    df = _get_dataset()
    recs = get_redistribution_recommendations(df, limit=8)
    return {
        "recommendations_count": len(recs),
        "priority_redistributions": recs[["Food_ID", "Food_Name", "Quantity", "City", "Provider", "Shelf_Life_Status", "Recommended_Receiver", "Receiver_Type", "Match_Confidence", "AI_Rationale"]].to_dict(orient="records")
    }

def get_all_food_tools() -> List[Any]:
    """Returns the list of all analytical LangChain tools."""
    return [
        get_food_statistics,
        get_unclaimed_food,
        get_expiring_food,
        get_provider_statistics,
        get_receiver_statistics,
        get_claims_statistics,
        get_city_food_waste_summary,
        get_redistribution_candidates
    ]
