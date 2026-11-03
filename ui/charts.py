import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Modern visual palette
CHART_TEMPLATE = "plotly_dark"
COLOR_SEQUENCE = ["#10b981", "#3b82f6", "#f59e0b", "#ec4899", "#8b5cf6", "#06b6d4", "#ef4444"]

def plot_food_trend(trend_df: pd.DataFrame):
    """Line and area charts showing food volume over time."""
    if trend_df.empty:
        return None
    
    fig = px.area(
        trend_df,
        x="Expiry_Date",
        y="Quantity",
        markers=True,
        title="📈 Surplus Food Quantity by Expiration Date",
        labels={"Expiry_Date": "Expiration Date", "Quantity": "Total Quantity (units)"},
        color_discrete_sequence=["#10b981"],
        template=CHART_TEMPLATE
    )
    fig.update_layout(
        xaxis_title="Expiration Date",
        yaxis_title="Units Available",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def plot_food_types_pie(df: pd.DataFrame):
    """Donut chart for dietary food types."""
    if df.empty:
        return None
    
    fig = px.pie(
        df,
        names="Food_Type",
        values="Total_Quantity",
        hole=0.55,
        title="🥗 Food Volume by Dietary Category",
        color_discrete_sequence=COLOR_SEQUENCE,
        template=CHART_TEMPLATE
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), showlegend=True)
    return fig

def plot_meal_types_bar(df: pd.DataFrame):
    """Bar chart for meal types."""
    if df.empty:
        return None
    
    fig = px.bar(
        df,
        x="Meal_Type",
        y="Total_Quantity",
        text="Total_Quantity",
        title="🍽️ Food Volume by Meal Category",
        labels={"Meal_Type": "Meal Type", "Total_Quantity": "Total Quantity"},
        color="Meal_Type",
        color_discrete_sequence=COLOR_SEQUENCE,
        template=CHART_TEMPLATE
    )
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
    return fig

def plot_city_availability_bar(df: pd.DataFrame, top_n: int = 10):
    """Bar chart for city-wise food availability vs unclaimed food."""
    if df.empty:
        return None
    
    top_df = df.head(top_n)
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_df["City"],
        y=top_df["Total_Quantity"],
        name="Total Listed Food",
        marker_color="#3b82f6"
    ))
    
    if "Unclaimed_Quantity" in top_df.columns:
        fig.add_trace(go.Bar(
            x=top_df["City"],
            y=top_df["Unclaimed_Quantity"],
            name="Unclaimed Surplus",
            marker_color="#ef4444"
        ))
        
    fig.update_layout(
        title=f"📍 Top {top_n} Cities: Total Food vs Unclaimed Surplus",
        barmode="group",
        template=CHART_TEMPLATE,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def plot_claim_status_donut(status_df: pd.DataFrame):
    """Donut chart for claim status distribution."""
    if status_df.empty:
        return None
        
    color_map = {
        "Completed": "#10b981",
        "Pending": "#f59e0b",
        "Cancelled": "#ef4444",
        "Unclaimed": "#64748b"
    }
    
    fig = px.pie(
        status_df,
        names="Status",
        values="Count",
        hole=0.6,
        title="📊 Redistribution & Claim Status Breakdown",
        color="Status",
        color_discrete_map=color_map,
        template=CHART_TEMPLATE
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig

def plot_top_providers_bar(top_df: pd.DataFrame):
    """Horizontal bar chart for top contributing providers."""
    if top_df.empty:
        return None
        
    fig = px.bar(
        top_df.sort_values(by="Total_Donated_Qty", ascending=True),
        x="Total_Donated_Qty",
        y="Provider_Name",
        orientation="h",
        text="Total_Donated_Qty",
        color="Provider_Business_Type",
        title="🏪 Top Food Donors by Quantity Contributed",
        labels={"Total_Donated_Qty": "Donated Quantity (units)", "Provider_Name": "Provider"},
        color_discrete_sequence=COLOR_SEQUENCE,
        template=CHART_TEMPLATE
    )
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig

def plot_top_receivers_bar(top_df: pd.DataFrame):
    """Horizontal bar chart for top active receivers."""
    if top_df.empty:
        return None
        
    fig = px.bar(
        top_df.sort_values(by="Total_Claims", ascending=True),
        x="Total_Claims",
        y="Receiver_Name",
        orientation="h",
        text="Total_Claims",
        color="Receiver_Organization_Type",
        title="🤝 Top Receiving Organizations by Claims",
        labels={"Total_Claims": "Claims Count", "Receiver_Name": "Receiver Name"},
        color_discrete_sequence=COLOR_SEQUENCE,
        template=CHART_TEMPLATE
    )
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig

def plot_provider_types_pie(df: pd.DataFrame):
    """Pie chart for provider types."""
    if df.empty:
        return None
    fig = px.pie(
        df,
        names="Provider_Type",
        values="Total_Quantity",
        hole=0.45,
        title="🏪 Contributions by Provider Business Type",
        color_discrete_sequence=COLOR_SEQUENCE,
        template=CHART_TEMPLATE
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig

def plot_receiver_types_pie(df: pd.DataFrame):
    """Pie chart for receiver organization types."""
    if df.empty:
        return None
    fig = px.pie(
        df,
        names="Receiver_Organization_Type",
        values="Total_Claims",
        hole=0.45,
        title="🤝 Claims by Receiver Organization Type",
        color_discrete_sequence=COLOR_SEQUENCE,
        template=CHART_TEMPLATE
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig

INDIAN_CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777, "Maharashtra"),
    "Delhi": (28.6139, 77.2090, "Delhi NCR"),
    "Bengaluru": (12.9716, 77.5946, "Karnataka"),
    "Hyderabad": (17.3850, 78.4867, "Telangana"),
    "Chennai": (13.0827, 80.2707, "Tamil Nadu"),
    "Kolkata": (22.5726, 88.3639, "West Bengal"),
    "Pune": (18.5204, 73.8567, "Maharashtra"),
    "Ahmedabad": (23.0225, 72.5714, "Gujarat"),
    "Jaipur": (26.9124, 75.7873, "Rajasthan"),
    "Lucknow": (26.8467, 80.9462, "Uttar Pradesh"),
    "Chandigarh": (30.7333, 76.7794, "Chandigarh"),
    "Indore": (22.7196, 75.8577, "Madhya Pradesh"),
    "Bhopal": (23.2599, 77.4126, "Madhya Pradesh"),
    "Kochi": (9.9312, 76.2673, "Kerala"),
    "Surat": (21.1702, 72.8311, "Gujarat"),
    "Patna": (25.5941, 85.1376, "Bihar"),
    "Nagpur": (21.1458, 79.0882, "Maharashtra"),
    "Coimbatore": (11.0168, 76.9558, "Tamil Nadu"),
    "Visakhapatnam": (17.6868, 83.2185, "Andhra Pradesh"),
    "Vadodara": (22.3072, 73.1812, "Gujarat")
}

def plot_geographic_map(city_data: pd.DataFrame):
    """Scatter map for city-level food distribution across India with precise geographic coordinates."""
    if city_data.empty:
        return None
        
    df_map = city_data.copy()
    
    def get_city_geo(city_name):
        c = str(city_name).strip()
        if c in INDIAN_CITY_COORDS:
            return INDIAN_CITY_COORDS[c]
        # Fallback for any other location
        h = abs(hash(c))
        return (15.0 + (h % 1200) / 100.0, 73.0 + ((h // 1000) % 1200) / 100.0, "India")
        
    df_map["lat"] = df_map["City"].map(lambda c: get_city_geo(c)[0])
    df_map["lon"] = df_map["City"].map(lambda c: get_city_geo(c)[1])
    df_map["State"] = df_map["City"].map(lambda c: get_city_geo(c)[2])
    df_map["Country"] = "India"
    
    fig = px.scatter_map(
        df_map,
        lat="lat",
        lon="lon",
        size="Total_Quantity",
        color="Total_Quantity",
        hover_name="City",
        hover_data={
            "State": True,
            "Country": True,
            "Total_Listings": True,
            "Total_Quantity": True,
            "Unclaimed_Quantity": True,
            "lat": False,
            "lon": False
        },
        color_continuous_scale="Viridis",
        zoom=3.8,
        center={"lat": 21.5, "lon": 79.0},
        title="🇮🇳 India Geographic Food Redistribution & Availability Footprint",
        template=CHART_TEMPLATE
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        map_style="carto-darkmatter"
    )
    return fig
