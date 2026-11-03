import os
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from database.connection import run_query

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"

def _load_from_csv(filename: str) -> pd.DataFrame:
    """Fallback loader for CSV datasets."""
    file_path = DATASET_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    return pd.read_csv(file_path)

def load_food_listings(use_db: bool = True) -> pd.DataFrame:
    """
    Loads food listings data from PostgreSQL database with CSV fallback.
    Columns: Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type
    """
    if use_db:
        try:
            df = run_query("SELECT * FROM food_listings_data")
            if not df.empty:
                return df
        except Exception:
            pass
    return _load_from_csv("food_listings_data.csv")

def load_providers(use_db: bool = True) -> pd.DataFrame:
    """
    Loads providers data from PostgreSQL database with CSV fallback.
    Columns: Provider_ID, Name, Type, Address, City, Contact
    """
    if use_db:
        try:
            df = run_query("SELECT * FROM providers_data")
            if not df.empty:
                return df
        except Exception:
            pass
    return _load_from_csv("providers_data.csv")

def load_receivers(use_db: bool = True) -> pd.DataFrame:
    """
    Loads receivers data from PostgreSQL database with CSV fallback.
    Columns: Receiver_ID, Name, Type, City, Contact
    """
    if use_db:
        try:
            df = run_query("SELECT * FROM receivers_data")
            if not df.empty:
                return df
        except Exception:
            pass
    return _load_from_csv("receivers_data.csv")

def load_claims(use_db: bool = True) -> pd.DataFrame:
    """
    Loads claims data from PostgreSQL database with CSV fallback.
    Columns: Claim_ID, Food_ID, Receiver_ID, Status, Timestamp
    """
    if use_db:
        try:
            df = run_query("SELECT * FROM claims_data")
            if not df.empty:
                return df
        except Exception:
            pass
    return _load_from_csv("claims_data.csv")

def clean_and_enrich_data(
    food_df: pd.DataFrame,
    prov_df: pd.DataFrame,
    recv_df: pd.DataFrame,
    claims_df: pd.DataFrame,
    reference_date: datetime = None
) -> pd.DataFrame:
    """
    Integrates the 4 datasets using relational LEFT JOINs and performs thorough data cleaning:
    1. Food Listings + Providers (on Provider_ID)
    2. Result + Claims (on Food_ID, preserving unclaimed listings)
    3. Result + Receivers (on Receiver_ID)
    4. Cleans datetimes, quantities, city strings, and computes shelf life & waste indicators.
    """
    # 1. Clean individual table columns before joining
    f_df = food_df.copy()
    p_df = prov_df.copy()
    r_df = recv_df.copy()
    c_df = claims_df.copy()

    # Rename provider & receiver columns to avoid collision
    p_df = p_df.rename(columns={
        "Name": "Provider_Name",
        "Type": "Provider_Business_Type",
        "Address": "Provider_Address",
        "City": "Provider_City",
        "Contact": "Provider_Contact",
        "Country": "Provider_Country"
    })

    r_df = r_df.rename(columns={
        "Name": "Receiver_Name",
        "Type": "Receiver_Organization_Type",
        "City": "Receiver_City",
        "Contact": "Receiver_Contact",
        "Country": "Receiver_Country"
    })

    c_df = c_df.rename(columns={
        "Status": "Claim_Status",
        "Timestamp": "Claim_Timestamp"
    })

    # Ensure key columns have consistent integer / numeric types
    for df, col in [(f_df, "Food_ID"), (f_df, "Provider_ID"),
                    (p_df, "Provider_ID"),
                    (r_df, "Receiver_ID"),
                    (c_df, "Claim_ID"), (c_df, "Food_ID"), (c_df, "Receiver_ID")]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Format numeric quantity
    f_df["Quantity"] = pd.to_numeric(f_df["Quantity"], errors="coerce").fillna(0).astype(int)

    # Standardize string fields
    string_cols = ["Food_Name", "Location", "Food_Type", "Meal_Type", "Provider_Type"]
    for col in string_cols:
        if col in f_df.columns:
            f_df[col] = f_df[col].astype(str).str.strip()

    if "Provider_City" in p_df.columns:
        p_df["Provider_City"] = p_df["Provider_City"].astype(str).str.strip()
    if "Receiver_City" in r_df.columns:
        r_df["Receiver_City"] = r_df["Receiver_City"].astype(str).str.strip()

    # Step A: Food + Provider
    food_provider = pd.merge(
        f_df,
        p_df,
        on="Provider_ID",
        how="left"
    )

    # Step B: (Food + Provider) + Claims (LEFT JOIN to keep ALL food listings, including unclaimed!)
    food_claim = pd.merge(
        food_provider,
        c_df,
        on="Food_ID",
        how="left"
    )

    # Step C: ((Food + Provider) + Claims) + Receivers
    integrated = pd.merge(
        food_claim,
        r_df,
        on="Receiver_ID",
        how="left"
    )

    # 2. Date Parsing
    integrated["Expiry_Date_Parsed"] = pd.to_datetime(integrated["Expiry_Date"], format='mixed', errors="coerce")
    integrated["Claim_Timestamp_Parsed"] = pd.to_datetime(integrated["Claim_Timestamp"], format='mixed', errors="coerce")

    # Reference date for expiry calculation
    if reference_date is None:
        # If dataset dates are from a specific range (e.g. March 2025), use the min expiry date or current date
        valid_expiries = integrated["Expiry_Date_Parsed"].dropna()
        if not valid_expiries.empty:
            min_exp = valid_expiries.min()
            today = pd.Timestamp.now()
            # If dataset is historical (e.g. 2025), set reference to the dataset's start date
            if min_exp < today - pd.Timedelta(days=180):
                reference_date = min_exp
            else:
                reference_date = today
        else:
            reference_date = pd.Timestamp.now()

    ref_ts = pd.to_datetime(reference_date)
    integrated["Days_To_Expiry"] = (integrated["Expiry_Date_Parsed"] - ref_ts).dt.days

    # 3. Status standardization
    integrated["Claim_Status_Clean"] = integrated["Claim_Status"].fillna("Unclaimed")
    integrated["Is_Claimed"] = integrated["Claim_Status_Clean"].isin(["Completed", "Pending"])
    integrated["Is_Completed"] = integrated["Claim_Status_Clean"] == "Completed"
    integrated["Is_Unclaimed"] = integrated["Claim_Status_Clean"] == "Unclaimed"

    # 4. Shelf Life & Risk Category
    def categorize_shelf_life(days):
        if pd.isna(days):
            return "Unknown"
        if days < 0:
            return "Expired"
        elif days <= 2:
            return "Critical (<48h)"
        elif days <= 7:
            return "Approaching Expiry (3-7d)"
        else:
            return "Fresh (>7d)"

    integrated["Shelf_Life_Status"] = integrated["Days_To_Expiry"].apply(categorize_shelf_life)

    # 5. Redistribution Priority Index
    def compute_redistribution_priority(row):
        if row["Is_Completed"]:
            return "Resolved (Claimed)"
        if row["Shelf_Life_Status"] == "Expired":
            return "Expired (Compost/Dispose)"
        if row["Shelf_Life_Status"] == "Critical (<48h)" and row["Quantity"] >= 20:
            return "High Priority (Urgent Action)"
        if row["Shelf_Life_Status"] == "Critical (<48h)" or (row["Shelf_Life_Status"] == "Approaching Expiry (3-7d)" and row["Quantity"] >= 25):
            return "High Priority"
        if row["Shelf_Life_Status"] == "Approaching Expiry (3-7d)":
            return "Medium Priority"
        return "Normal / Available"

    integrated["Redistribution_Priority"] = integrated.apply(compute_redistribution_priority, axis=1)

    # Unified City column (fall back from Location to Provider_City)
    integrated["City"] = integrated["Location"].fillna(integrated.get("Provider_City", "Mumbai"))
    if "Country" not in integrated.columns or integrated["Country"].isnull().all():
        integrated["Country"] = "India"
    else:
        integrated["Country"] = integrated["Country"].fillna("India")

    return integrated

def create_integrated_dataset(use_db: bool = True) -> pd.DataFrame:
    """
    Convenience function to load all 4 tables and return the fully integrated, cleaned dataset.
    """
    food_df = load_food_listings(use_db=use_db)
    prov_df = load_providers(use_db=use_db)
    recv_df = load_receivers(use_db=use_db)
    claims_df = load_claims(use_db=use_db)
    
    return clean_and_enrich_data(food_df, prov_df, recv_df, claims_df)

def get_dataset_summary(df: pd.DataFrame) -> dict:
    """Returns a high-level statistical dictionary of the dataset."""
    total_listings = len(df["Food_ID"].unique())
    total_qty = int(df.drop_duplicates(subset=["Food_ID"])["Quantity"].sum())
    unique_providers = len(df["Provider_ID"].dropna().unique())
    unique_receivers = len(df["Receiver_ID"].dropna().unique())
    
    completed_claims = int((df["Claim_Status_Clean"] == "Completed").sum())
    unclaimed_listings = int((df["Claim_Status_Clean"] == "Unclaimed").sum())
    pending_claims = int((df["Claim_Status_Clean"] == "Pending").sum())
    cancelled_claims = int((df["Claim_Status_Clean"] == "Cancelled").sum())

    return {
        "total_food_listings": total_listings,
        "total_food_quantity": total_qty,
        "unique_providers": unique_providers,
        "unique_receivers": unique_receivers,
        "completed_claims": completed_claims,
        "unclaimed_listings": unclaimed_listings,
        "pending_claims": pending_claims,
        "cancelled_claims": cancelled_claims,
        "claim_fulfillment_rate_pct": round((completed_claims / total_listings * 100), 1) if total_listings > 0 else 0,
        "unclaimed_rate_pct": round((unclaimed_listings / total_listings * 100), 1) if total_listings > 0 else 0,
    }
