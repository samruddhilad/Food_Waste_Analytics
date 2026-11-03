import streamlit as st
import pandas as pd
from datetime import datetime

from database.connection import test_connection
from data.processing import create_integrated_dataset
from ui.styles import inject_custom_css
from ui.dashboard import render_dashboard

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Food Waste Analytics & Redistribution System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom modern glassmorphic styling
inject_custom_css()

# =========================================================
# 2. HEADER
# =========================================================
st.markdown('<div class="main-header">🍽️ Food Waste Analytics & Redistribution System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header"><span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 10px; border-radius: 8px; font-weight: 600; color: #34d399; margin-right: 8px;">🇮🇳 India National Edition</span> Intelligent Surplus Tracking, Waste Reduction & AI Redistribution</div>', unsafe_allow_html=True)

# =========================================================
# 3. DATABASE CONNECTION & DATA INITIALIZATION
# =========================================================
# Run data pipeline FIRST and completely independently of AI
is_connected, status_msg, _ = test_connection()

try:
    raw_df = create_integrated_dataset(use_db=is_connected)
except Exception as e:
    st.error(f"Error loading database records: {str(e)}")
    # Fallback to local CSV dataset
    raw_df = create_integrated_dataset(use_db=False)

# =========================================================
# 4. SIDEBAR CONTROLS & FILTERS
# =========================================================
with st.sidebar:
    st.markdown("### ⚙️ Database & System Status")
    
    if is_connected:
        st.success(f"🟢 **PostgreSQL Connected**\n\n{status_msg}\n\n📊 *Live Database Source:* **{len(raw_df):,}** integrated rows")
    else:
        st.warning(f"🟡 **PostgreSQL Offline (Fallback Mode)**\n\n{status_msg}\n\n📦 *Running on local CSV fallback dataset ({len(raw_df):,} rows).*")
        
    st.markdown("---")
    
    # Regional Scope
    st.markdown("### 📍 Regional Scope")
    st.markdown("🌐 **Country:** `India` *(20 Major Urban Hubs)*")
    st.markdown(f"🏙️ **Active Cities:** `{raw_df['City'].nunique()} Cities` across India")
    
    st.markdown("---")

    # AI Engine Configuration (Optional - Never blocks the dashboard)
    st.markdown("### 🤖 AI LLM Setup")
    provider_choice = st.selectbox("LLM Provider", ["Auto-detect (.env)", "Google Gemini", "OpenAI"])
    api_key_input = st.text_input("Custom Gemini/OpenAI API Key (Optional)", type="password", help="Leave blank if configured in .env")
    
    st.session_state["llm_provider_choice"] = None if provider_choice == "Auto-detect (.env)" else provider_choice
    st.session_state["custom_api_key"] = api_key_input.strip() if api_key_input else None

    st.markdown("---")
    
    def reset_all_filters():
        st.session_state["filter_cities"] = []
        st.session_state["filter_food_types"] = []
        st.session_state["filter_meal_types"] = []
        st.session_state["filter_statuses"] = []

    # 100% Dynamic Filters from the actual loaded dataset
    st.markdown("### 🔍 Dataset Filters")
    
    all_cities = sorted([str(c) for c in raw_df["City"].dropna().unique() if str(c).strip()])
    all_food_types = sorted([str(f) for f in raw_df["Food_Type"].dropna().unique() if str(f).strip()]) if "Food_Type" in raw_df.columns else []
    all_meal_types = sorted([str(m) for m in raw_df["Meal_Type"].dropna().unique() if str(m).strip()]) if "Meal_Type" in raw_df.columns else []
    all_statuses = sorted([str(s) for s in raw_df["Shelf_Life_Status"].dropna().unique() if str(s).strip()]) if "Shelf_Life_Status" in raw_df.columns else []
    
    selected_cities = st.multiselect("Filter City / Location", options=all_cities, key="filter_cities")
    selected_food_types = st.multiselect("Filter Food Type", options=all_food_types, key="filter_food_types")
    selected_meal_types = st.multiselect("Filter Meal Type", options=all_meal_types, key="filter_meal_types")
    selected_statuses = st.multiselect("Filter Shelf Life Status", options=all_statuses, key="filter_statuses")

    st.button("🔄 Reset Filters", on_click=reset_all_filters, use_container_width=True)

# =========================================================
# 5. APPLY DYNAMIC FILTERS TO DATASET
# =========================================================
filtered_df = raw_df.copy()

if selected_cities:
    filtered_df = filtered_df[filtered_df["City"].isin(selected_cities)]
if selected_food_types:
    filtered_df = filtered_df[filtered_df["Food_Type"].isin(selected_food_types)]
if selected_meal_types:
    filtered_df = filtered_df[filtered_df["Meal_Type"].isin(selected_meal_types)]
if selected_statuses:
    filtered_df = filtered_df[filtered_df["Shelf_Life_Status"].isin(selected_statuses)]

# Clean handling when filters produce zero records
has_active_filters = bool(selected_cities or selected_food_types or selected_meal_types or selected_statuses)
if filtered_df.empty and has_active_filters:
    st.warning("⚠️ **No food surplus records match the selected filter combination.**")
    active_criteria = []
    if selected_cities: active_criteria.append(f"**City:** {', '.join(selected_cities)}")
    if selected_food_types: active_criteria.append(f"**Food Type:** {', '.join(selected_food_types)}")
    if selected_meal_types: active_criteria.append(f"**Meal Type:** {', '.join(selected_meal_types)}")
    if selected_statuses: active_criteria.append(f"**Status:** {', '.join(selected_statuses)}")
    st.info(f"🔎 Selected criteria: {' | '.join(active_criteria)}.\n\nTry removing one filter to view matching records, or click below to reset.")
    st.button("🔄 Clear Filters & Show All Listings", on_click=reset_all_filters, key="clear_zero_filters_main")

# =========================================================
# 6. RENDER DASHBOARD TABS
# =========================================================
render_dashboard(filtered_df, is_connected, status_msg)

# =========================================================
# 7. FOOTER
# =========================================================
st.markdown("---")
st.markdown(
    f"<center style='color:#64748b; font-size:0.85rem;'>"
    f"🚀 Intelligent Food Waste Analytics & Redistribution Dashboard | "
    f"🕒 Live Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Powered by Streamlit, Pandas, PostgreSQL, Plotly, LangChain & LangGraph"
    f"</center>",
    unsafe_allow_html=True
)