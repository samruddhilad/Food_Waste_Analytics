import pandas as pd
import numpy as np

def compute_kpi_metrics(df: pd.DataFrame) -> dict:
    """Computes high-level KPI cards data for the dashboard."""
    # Dedup on Food_ID for listings-level metrics
    unique_food_df = df.drop_duplicates(subset=["Food_ID"])
    
    total_listings = int(len(unique_food_df))
    total_qty = int(unique_food_df["Quantity"].sum()) if not unique_food_df.empty else 0
    total_providers = int(df["Provider_ID"].dropna().nunique())
    total_receivers = int(df["Receiver_ID"].dropna().nunique())
    
    # Claims metrics
    claims_df = df.dropna(subset=["Claim_ID"]).drop_duplicates(subset=["Claim_ID"])
    total_claims = int(len(claims_df))
    completed_claims = int((claims_df["Claim_Status_Clean"] == "Completed").sum())
    pending_claims = int((claims_df["Claim_Status_Clean"] == "Pending").sum())
    cancelled_claims = int((claims_df["Claim_Status_Clean"] == "Cancelled").sum())
    
    # Waste / Unclaimed metrics
    unclaimed_df = df[df["Claim_Status_Clean"] == "Unclaimed"]
    unclaimed_qty = int(unclaimed_df.drop_duplicates(subset=["Food_ID"])["Quantity"].sum())
    
    # Expired / Critical metrics
    critical_df = unique_food_df[unique_food_df["Shelf_Life_Status"] == "Critical (<48h)"]
    critical_qty = int(critical_df["Quantity"].sum()) if not critical_df.empty else 0
    
    expired_df = unique_food_df[unique_food_df["Shelf_Life_Status"] == "Expired"]
    expired_qty = int(expired_df["Quantity"].sum()) if not expired_df.empty else 0

    claim_rate = round((completed_claims / total_listings * 100), 1) if total_listings > 0 else 0
    unclaimed_rate = round((len(unclaimed_df) / total_listings * 100), 1) if total_listings > 0 else 0

    return {
        "total_listings": total_listings,
        "total_quantity": total_qty,
        "total_providers": total_providers,
        "total_receivers": total_receivers,
        "total_claims": total_claims,
        "completed_claims": completed_claims,
        "pending_claims": pending_claims,
        "cancelled_claims": cancelled_claims,
        "unclaimed_quantity": unclaimed_qty,
        "critical_quantity": critical_qty,
        "expired_quantity": expired_qty,
        "claim_rate_pct": claim_rate,
        "unclaimed_rate_pct": unclaimed_rate,
        "estimated_meals_potential": int(total_qty * 2.5),
        "estimated_meals_saved": int((total_qty - unclaimed_qty) * 2.5) if (total_qty - unclaimed_qty) > 0 else 0
    }

def get_food_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates food quantities and listings by food type (Dietary category)."""
    unique_food = df.drop_duplicates(subset=["Food_ID"])
    if unique_food.empty or "Food_Type" not in unique_food.columns:
        return pd.DataFrame(columns=["Food_Type", "Listing_Count", "Total_Quantity", "Avg_Quantity"])
    
    res = unique_food.groupby("Food_Type").agg(
        Listing_Count=("Food_ID", "count"),
        Total_Quantity=("Quantity", "sum"),
        Avg_Quantity=("Quantity", "mean")
    ).reset_index()
    res["Avg_Quantity"] = res["Avg_Quantity"].round(1)
    return res.sort_values(by="Total_Quantity", ascending=False)

def get_meal_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates food quantities and listings by meal type (Breakfast, Lunch, Dinner, etc.)."""
    unique_food = df.drop_duplicates(subset=["Food_ID"])
    if unique_food.empty or "Meal_Type" not in unique_food.columns:
        return pd.DataFrame(columns=["Meal_Type", "Listing_Count", "Total_Quantity"])
    
    res = unique_food.groupby("Meal_Type").agg(
        Listing_Count=("Food_ID", "count"),
        Total_Quantity=("Quantity", "sum")
    ).reset_index()
    return res.sort_values(by="Total_Quantity", ascending=False)

def get_city_food_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates food listings, total quantity, and unclaimed food by City/Location."""
    unique_food = df.drop_duplicates(subset=["Food_ID"])
    if unique_food.empty:
        return pd.DataFrame(columns=["City", "Total_Listings", "Total_Quantity", "Unclaimed_Quantity"])
    
    city_col = "Location" if "Location" in unique_food.columns else "City"
    grouped = unique_food.groupby(city_col).agg(
        Total_Listings=("Food_ID", "count"),
        Total_Quantity=("Quantity", "sum"),
        Unclaimed_Quantity=("Quantity", lambda q: unique_food.loc[q.index][unique_food.loc[q.index, "Claim_Status_Clean"] == "Unclaimed"]["Quantity"].sum())
    ).reset_index().rename(columns={city_col: "City"})
    
    return grouped.sort_values(by="Total_Quantity", ascending=False)

def get_expiry_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Groups food quantity over Expiry_Date."""
    unique_food = df.drop_duplicates(subset=["Food_ID"]).copy()
    if unique_food.empty or "Expiry_Date_Parsed" not in unique_food.columns:
        return pd.DataFrame(columns=["Expiry_Date", "Quantity", "Listings"])
    
    valid = unique_food.dropna(subset=["Expiry_Date_Parsed"])
    if valid.empty:
        return pd.DataFrame(columns=["Expiry_Date", "Quantity", "Listings"])
    
    grouped = valid.groupby("Expiry_Date_Parsed").agg(
        Quantity=("Quantity", "sum"),
        Listings=("Food_ID", "count")
    ).reset_index().rename(columns={"Expiry_Date_Parsed": "Expiry_Date"})
    
    return grouped.sort_values(by="Expiry_Date")

def get_top_providers(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Identifies the top food providers by donated quantity and completed claims."""
    unique_food = df.drop_duplicates(subset=["Food_ID"]).copy()
    if unique_food.empty:
        return pd.DataFrame()
    
    grouped = unique_food.groupby(["Provider_ID", "Provider_Name", "Provider_Business_Type", "City"]).agg(
        Total_Donated_Qty=("Quantity", "sum"),
        Total_Listings=("Food_ID", "count")
    ).reset_index()
    
    # Calculate completed claims
    completed = df[df["Claim_Status_Clean"] == "Completed"].groupby("Provider_ID")["Claim_ID"].nunique().reset_index().rename(columns={"Claim_ID": "Completed_Claims"})
    merged = pd.merge(grouped, completed, on="Provider_ID", how="left")
    merged["Completed_Claims"] = merged["Completed_Claims"].fillna(0).astype(int)
    
    return merged.sort_values(by="Total_Donated_Qty", ascending=False).head(top_n)

def get_provider_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates food contributions by provider category (Supermarket, Restaurant, Catering, Grocery)."""
    unique_food = df.drop_duplicates(subset=["Food_ID"])
    col = "Provider_Type" if "Provider_Type" in unique_food.columns else "Provider_Business_Type"
    if col not in unique_food.columns or unique_food.empty:
        return pd.DataFrame()
    
    return unique_food.groupby(col).agg(
        Total_Quantity=("Quantity", "sum"),
        Listing_Count=("Food_ID", "count")
    ).reset_index().rename(columns={col: "Provider_Type"}).sort_values(by="Total_Quantity", ascending=False)

def get_top_receivers(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Identifies top receivers by total claims and claimed quantity."""
    claims_df = df.dropna(subset=["Claim_ID"]).copy()
    if claims_df.empty:
        return pd.DataFrame()
    
    grouped = claims_df.groupby(["Receiver_ID", "Receiver_Name", "Receiver_Organization_Type", "Receiver_City"]).agg(
        Total_Claims=("Claim_ID", "nunique"),
        Completed_Claims=("Claim_Status_Clean", lambda s: (s == "Completed").sum()),
        Total_Quantity_Claimed=("Quantity", "sum")
    ).reset_index()
    
    return grouped.sort_values(by="Total_Claims", ascending=False).head(top_n)

def get_receiver_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates claim volume by receiver organization type (NGO, Shelter, Charity, Individual)."""
    claims_df = df.dropna(subset=["Claim_ID"])
    if claims_df.empty or "Receiver_Organization_Type" not in claims_df.columns:
        return pd.DataFrame()
    
    return claims_df.groupby("Receiver_Organization_Type").agg(
        Total_Claims=("Claim_ID", "nunique"),
        Total_Quantity=("Quantity", "sum")
    ).reset_index().sort_values(by="Total_Claims", ascending=False)

def get_claim_status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Computes distribution across Completed, Pending, Cancelled, and Unclaimed statuses."""
    counts = df["Claim_Status_Clean"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]
    total = counts["Count"].sum()
    counts["Percentage"] = (counts["Count"] / total * 100).round(1)
    return counts

def get_waste_indicators(df: pd.DataFrame) -> dict:
    """Computes specialized food waste and shelf-life indicators."""
    unique_food = df.drop_duplicates(subset=["Food_ID"])
    total_listings = len(unique_food)
    total_qty = unique_food["Quantity"].sum()
    
    unclaimed = unique_food[unique_food["Claim_Status_Clean"] == "Unclaimed"]
    unclaimed_qty = unclaimed["Quantity"].sum()
    
    critical = unique_food[unique_food["Shelf_Life_Status"] == "Critical (<48h)"]
    critical_qty = critical["Quantity"].sum()
    
    expired = unique_food[unique_food["Shelf_Life_Status"] == "Expired"]
    expired_qty = expired["Quantity"].sum()
    
    # Waste Risk Index: weighted formula of unclaimed and critical items
    risk_score = round(((unclaimed_qty * 0.6 + critical_qty * 0.4) / max(total_qty, 1)) * 100, 1)
    
    return {
        "total_quantity": int(total_qty),
        "unclaimed_quantity": int(unclaimed_qty),
        "unclaimed_percentage": round((unclaimed_qty / max(total_qty, 1)) * 100, 1),
        "critical_expiry_quantity": int(critical_qty),
        "expired_quantity": int(expired_qty),
        "waste_risk_index_score": min(risk_score, 100.0),
        "high_priority_redistribution_count": int(len(unique_food[unique_food["Redistribution_Priority"].str.contains("High", na=False)]))
    }

def get_redistribution_recommendations(df: pd.DataFrame, limit: int = 15) -> pd.DataFrame:
    """
    Algorithmic matching of high-urgency unclaimed food listings with suitable receivers in the same city.
    Ranks items by urgency, quantity, and receiver suitability.
    """
    # Filter for food that is unclaimed or pending, not yet expired or critical
    target_food = df[
        (df["Claim_Status_Clean"].isin(["Unclaimed", "Pending"])) &
        (df["Shelf_Life_Status"].isin(["Critical (<48h)", "Approaching Expiry (3-7d)", "Fresh (>7d)"]))
    ].drop_duplicates(subset=["Food_ID"]).copy()
    
    if target_food.empty:
        return pd.DataFrame()
        
    # Receiver pool
    receiver_pool = df.dropna(subset=["Receiver_ID", "Receiver_City"]).drop_duplicates(subset=["Receiver_ID"])
    
    recommendations = []
    for _, item in target_food.iterrows():
        food_city = item.get("Location") or item.get("Provider_City")
        food_name = item.get("Food_Name")
        food_qty = item.get("Quantity")
        shelf_life = item.get("Shelf_Life_Status")
        priority = item.get("Redistribution_Priority")
        food_type = item.get("Food_Type")
        provider_name = item.get("Provider_Name", "Unknown")
        
        # Match receivers in the same city
        matching_receivers = receiver_pool[receiver_pool["Receiver_City"] == food_city]
        
        if not matching_receivers.empty:
            # Prioritize NGOs and Shelters
            top_rec = matching_receivers.iloc[0]
            rec_name = top_rec.get("Receiver_Name", "Community Hub")
            rec_type = top_rec.get("Receiver_Organization_Type", "NGO")
            rec_contact = top_rec.get("Receiver_Contact", "N/A")
            match_confidence = "High (Local City Match)"
        else:
            rec_name = "Nearby Regional Relief Center"
            rec_type = "Shelter / NGO"
            rec_contact = "Available upon dispatch"
            match_confidence = "Medium (Regional Transfer)"
            
        reasoning = (
            f"Food item '{food_name}' ({food_qty} units, {food_type}) listed by '{provider_name}' "
            f"is currently {item.get('Claim_Status_Clean')}. Shelf life is '{shelf_life}'. "
            f"Recommended allocation to '{rec_name}' ({rec_type}) in {food_city} to prevent wastage."
        )
        
        recommendations.append({
            "Food_ID": item["Food_ID"],
            "Food_Name": food_name,
            "Quantity": food_qty,
            "City": food_city,
            "Provider": provider_name,
            "Shelf_Life_Status": shelf_life,
            "Priority": priority,
            "Recommended_Receiver": rec_name,
            "Receiver_Type": rec_type,
            "Receiver_Contact": rec_contact,
            "Match_Confidence": match_confidence,
            "AI_Rationale": reasoning
        })
        
    rec_df = pd.DataFrame(recommendations)
    
    # Sort by urgency: High Priority first, then by quantity descending
    priority_order = {
        "High Priority (Urgent Action)": 1,
        "High Priority": 2,
        "Medium Priority": 3,
        "Normal / Available": 4
    }
    rec_df["priority_rank"] = rec_df["Priority"].map(lambda p: priority_order.get(p, 5))
    rec_df = rec_df.sort_values(by=["priority_rank", "Quantity"], ascending=[True, False]).drop(columns=["priority_rank"])
    
    return rec_df.head(limit)
