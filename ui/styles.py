import streamlit as st

def inject_custom_css():
    """Injects high-end, responsive custom styling for modern glassmorphism aesthetics."""
    st.markdown("""
    <style>
    /* Global Typography and Canvas Styling */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Enforce Dark Background across all components & browsers */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
    }
    
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #111827 !important;
        color: #f8fafc !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Header Gradient text */
    .main-header {
        background: linear-gradient(90deg, #10b981, #06b6d4, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    
    .sub-header {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    
    /* Glassmorphic KPI Cards */
    .kpi-container {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 16px;
        text-align: center;
        color: #f8fafc;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 14px;
        position: relative;
        overflow: hidden;
    }
    
    .kpi-container:hover {
        transform: translateY(-3px);
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.4);
    }
    
    .kpi-top-bar {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.2;
    }
    
    .kpi-subtitle {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 6px;
    }
    
    /* Section Cards */
    .section-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 20px;
    }
    
    /* Custom Badges */
    .badge-urgent {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .badge-medium {
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .badge-success {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    /* Chat bubbles */
    .chat-bubble-user {
        background: linear-gradient(135deg, #1e3a8a, #1e40af);
        color: white;
        padding: 12px 16px;
        border-radius: 14px 14px 2px 14px;
        margin-bottom: 10px;
        display: inline-block;
        max-width: 85%;
        float: right;
        clear: both;
    }
    
    .chat-bubble-ai {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #f1f5f9;
        padding: 16px 20px;
        border-radius: 14px 14px 14px 2px;
        margin-bottom: 12px;
        max-width: 95%;
        float: left;
        clear: both;
    }

    /* Streamlit Tab Enhancements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

def render_kpi_card(title: str, value: str or int, icon: str = "📊", color: str = "#3b82f6", subtitle: str = "") -> str:
    """Returns HTML for a glassmorphism KPI card."""
    formatted_val = f"{value:,}" if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
    sub_html = f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ""
    return f"""
    <div class="kpi-container">
        <div class="kpi-top-bar" style="background: {color};"></div>
        <div class="kpi-title">{icon} {title}</div>
        <div class="kpi-value">{formatted_val}</div>
        {sub_html}
    </div>
    """

def render_badge(text: str, level: str = "info") -> str:
    """Returns HTML for a colored status badge."""
    level_classes = {
        "urgent": "badge-urgent",
        "danger": "badge-urgent",
        "warning": "badge-medium",
        "medium": "badge-medium",
        "success": "badge-success",
        "resolved": "badge-success"
    }
    css_class = level_classes.get(level.lower(), "badge-medium")
    return f'<span class="{css_class}">{text}</span>'
