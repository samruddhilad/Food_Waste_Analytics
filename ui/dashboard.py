import streamlit as st
import pandas as pd
from datetime import datetime

from ui.styles import render_kpi_card, render_badge
from ui.charts import (
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
from analytics.analytics import (
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
from database.queries import PREDEFINED_QUERIES
from database.connection import run_query
from ai.langgraph_workflow import run_food_waste_workflow
from ai.llm_factory import get_configured_llm_info

def render_dashboard(df: pd.DataFrame, is_db_connected: bool, db_status_msg: str):
    """
    Renders the complete 8-tab Streamlit dashboard interface.
    """
    # 1. Global Metrics Calculation
    kpis = compute_kpi_metrics(df)
    waste_metrics = get_waste_indicators(df)

    # 2. Main Tab Navigation
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Overview",
        "🍱 Food Analytics",
        "🏪 Provider Analytics",
        "🤝 Receiver Analytics",
        "📈 Claims Analytics",
        "🤖 AI Assistant",
        "🎯 Smart Recommendations",
        "🔍 SQL Insights"
    ])

    # =========================================================
    # TAB 1: OVERVIEW
    # =========================================================
    with tab1:
        st.markdown("### 📊 High-Level Performance & Waste Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(render_kpi_card("Total Listings", kpis["total_listings"], "📦", "#3b82f6", "Active registered food items"), unsafe_allow_html=True)
        col2.markdown(render_kpi_card("Total Food Units", kpis["total_quantity"], "🍱", "#10b981", f"~{kpis['estimated_meals_potential']:,} meal equivalents"), unsafe_allow_html=True)
        col3.markdown(render_kpi_card("Active Providers", kpis["total_providers"], "🏪", "#f59e0b", "Donating business entities"), unsafe_allow_html=True)
        col4.markdown(render_kpi_card("Total Claims", kpis["total_claims"], "📊", "#ec4899", f"{kpis['claim_rate_pct']}% claim rate"), unsafe_allow_html=True)

        st.markdown("---")

        # Second row of waste KPIs
        w1, w2, w3, w4 = st.columns(4)
        w1.markdown(render_kpi_card("Unclaimed Surplus", kpis["unclaimed_quantity"], "⚠️", "#ef4444", f"{kpis['unclaimed_rate_pct']}% of total volume"), unsafe_allow_html=True)
        w2.markdown(render_kpi_card("Critical Expiry (<48h)", kpis["critical_quantity"], "⏳", "#f97316", "Requires immediate dispatch"), unsafe_allow_html=True)
        w3.markdown(render_kpi_card("Completed Claims", kpis["completed_claims"], "✅", "#10b981", f"~{kpis['estimated_meals_saved']:,} meals rescued"), unsafe_allow_html=True)
        w4.markdown(render_kpi_card("Waste Risk Index", f"{waste_metrics['waste_risk_index_score']}/100", "🛡️", "#8b5cf6", "Composite urgency metric"), unsafe_allow_html=True)

        st.markdown("---")

        # Trend and City charts
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            trend_df = get_expiry_trend(df)
            fig_trend = plot_food_trend(trend_df)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True, key="overview_trend_chart")
            else:
                st.info("No temporal trend data available for current filters.")

        with t_col2:
            status_df = get_claim_status_distribution(df)
            fig_status = plot_claim_status_donut(status_df)
            if fig_status:
                st.plotly_chart(fig_status, use_container_width=True, key="overview_status_chart")

        # Geographic distribution
        st.markdown("---")
        st.markdown("#### 🌍 Geographic Redistribution Footprint")
        city_df = get_city_food_distribution(df)
        fig_map = plot_geographic_map(city_df)
        if fig_map:
            st.plotly_chart(fig_map, use_container_width=True, key="overview_geo_map_chart")

    # =========================================================
    # TAB 2: FOOD ANALYTICS
    # =========================================================
    with tab2:
        st.markdown("### 🍱 Food Listings & Inventory Breakdown")
        
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            food_type_df = get_food_type_distribution(df)
            fig_f_type = plot_food_types_pie(food_type_df)
            if fig_f_type:
                st.plotly_chart(fig_f_type, use_container_width=True, key="food_type_pie_chart")
                
        with f_col2:
            meal_type_df = get_meal_type_distribution(df)
            fig_meal = plot_meal_types_bar(meal_type_df)
            if fig_meal:
                st.plotly_chart(fig_meal, use_container_width=True, key="meal_type_bar_chart")

        st.markdown("---")
        st.markdown("#### 📍 City-Wise Food Availability & Surplus")
        fig_city = plot_city_availability_bar(city_df, top_n=10)
        if fig_city:
            st.plotly_chart(fig_city, use_container_width=True, key="city_availability_bar_chart")

        st.markdown("#### 📋 Detailed Food Listings Table")
        preview_cols = ["Food_ID", "Food_Name", "Quantity", "Food_Type", "Meal_Type", "Location", "Provider_Name", "Shelf_Life_Status", "Claim_Status_Clean", "Redistribution_Priority"]
        available_cols = [c for c in preview_cols if c in df.columns]
        st.dataframe(df[available_cols].drop_duplicates(subset=["Food_ID"]), use_container_width=True, hide_index=True)

    # =========================================================
    # TAB 3: PROVIDER ANALYTICS
    # =========================================================
    with tab3:
        st.markdown("### 🏪 Food Provider Contributions & Engagement")
        
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            prov_type_df = get_provider_type_distribution(df)
            fig_p_type = plot_provider_types_pie(prov_type_df)
            if fig_p_type:
                st.plotly_chart(fig_p_type, use_container_width=True, key="provider_type_pie_chart")
                
        with p_col2:
            top_prov_df = get_top_providers(df, top_n=10)
            fig_top_p = plot_top_providers_bar(top_prov_df)
            if fig_top_p:
                st.plotly_chart(fig_top_p, use_container_width=True, key="top_providers_bar_chart")

        st.markdown("---")
        st.markdown("#### 📋 Provider Leaderboard")
        if not top_prov_df.empty:
            st.dataframe(top_prov_df, use_container_width=True, hide_index=True)

    # =========================================================
    # TAB 4: RECEIVER ANALYTICS
    # =========================================================
    with tab4:
        st.markdown("### 🤝 Receiver Activity & Demand Distribution")
        
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            recv_type_df = get_receiver_type_distribution(df)
            fig_r_type = plot_receiver_types_pie(recv_type_df)
            if fig_r_type:
                st.plotly_chart(fig_r_type, use_container_width=True, key="receiver_type_pie_chart")
                
        with r_col2:
            top_recv_df = get_top_receivers(df, top_n=10)
            fig_top_r = plot_top_receivers_bar(top_recv_df)
            if fig_top_r:
                st.plotly_chart(fig_top_r, use_container_width=True, key="top_receivers_bar_chart")

        st.markdown("---")
        st.markdown("#### 📋 Top Receiver Directory")
        if not top_recv_df.empty:
            st.dataframe(top_recv_df, use_container_width=True, hide_index=True)

    # =========================================================
    # TAB 5: CLAIMS ANALYTICS
    # =========================================================
    with tab5:
        st.markdown("### 📈 Redistribution Claims Performance")
        
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            fig_claim_donut = plot_claim_status_donut(status_df)
            if fig_claim_donut:
                st.plotly_chart(fig_claim_donut, use_container_width=True, key="claims_status_donut_chart")
                
        with c_col2:
            st.markdown("#### 🎯 Claim Conversion Health")
            st.write(f"- **Total Claims Initiated:** `{kpis['total_claims']:,}`")
            st.write(f"- **Successfully Completed:** `{kpis['completed_claims']:,}` ({kpis['claim_rate_pct']}%)")
            st.write(f"- **Pending Allocation:** `{kpis['pending_claims']:,}`")
            st.write(f"- **Cancelled Claims:** `{kpis['cancelled_claims']:,}`")
            st.write(f"- **Unclaimed Surplus Listings:** `{waste_metrics['unclaimed_quantity']:,} units`")
            
            st.progress(min(kpis['claim_rate_pct'] / 100.0, 1.0))
            st.caption("Rescued vs Unclaimed conversion efficiency")

        st.markdown("---")
        st.markdown("#### 📋 Recent Claims Transactions")
        claims_preview = df.dropna(subset=["Claim_ID"])[["Claim_ID", "Food_ID", "Food_Name", "Quantity", "Receiver_Name", "Receiver_Organization_Type", "Claim_Status_Clean", "Claim_Timestamp"]].drop_duplicates(subset=["Claim_ID"])
        st.dataframe(claims_preview.head(50), use_container_width=True, hide_index=True)

    # =========================================================
    # TAB 6: AI ASSISTANT (LANGCHAIN + LANGGRAPH)
    # =========================================================
    with tab6:
        st.markdown("### 🤖 Intelligent Food Redistribution AI Assistant")
        st.caption("Powered by **LangChain** tool orchestration and **LangGraph** multi-step state graph execution.")

        llm_label, is_llm_active = get_configured_llm_info(
            custom_key=st.session_state.get("custom_api_key"),
            provider_choice=st.session_state.get("llm_provider_choice")
        )
        
        if is_llm_active:
            st.success(f"⚡ Active AI Engine: **{llm_label}**")
        else:
            st.info("💡 Running in **Rule-Based Deterministic NLP Mode**. Add a Google Gemini or OpenAI API key in the sidebar for generative natural language.")

        # Quick question chips
        st.markdown("##### 💡 Suggested Questions:")
        suggestions = [
            "Which city has the most unclaimed food?",
            "Which providers contribute the most food?",
            "Which food items are approaching expiry?",
            "Which receivers have claimed the most food?",
            "Give me a summary of the current food waste situation.",
            "Which food should be prioritized for redistribution?"
        ]
        
        col_s1, col_s2, col_s3 = st.columns(3)
        for i, q in enumerate(suggestions):
            target_col = col_s1 if i % 3 == 0 else (col_s2 if i % 3 == 1 else col_s3)
            if target_col.button(q, key=f"chip_{i}"):
                st.session_state["user_input_ai"] = q

        # Chat history container
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        user_query = st.chat_input("Ask any question regarding food waste, providers, receivers, or redistribution...")
        
        # Check if set via button
        if "user_input_ai" in st.session_state and st.session_state["user_input_ai"]:
            user_query = st.session_state["user_input_ai"]
            st.session_state["user_input_ai"] = None

        if user_query:
            st.session_state["chat_history"].append({"role": "user", "content": user_query})
            with st.spinner("Analyzing data through LangGraph workflow..."):
                workflow_output = run_food_waste_workflow(
                    question=user_query,
                    df=df,
                    custom_key=st.session_state.get("custom_api_key"),
                    provider_choice=st.session_state.get("llm_provider_choice")
                )
                ai_response = workflow_output.get("final_response", "Unable to generate response.")
                intent = workflow_output.get("intent", "general")
                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": ai_response,
                    "intent": intent,
                    "provider": workflow_output.get("llm_provider", "Deterministic")
                })

        # Render conversation history
        for msg in reversed(st.session_state["chat_history"]):
            if msg["role"] == "user":
                st.chat_message("user").markdown(f"**{msg['content']}**")
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
                    if "intent" in msg:
                        st.caption(f"🎯 Intent: `{msg['intent']}` | Engine: `{msg.get('provider')}`")

    # =========================================================
    # TAB 7: SMART RECOMMENDATIONS
    # =========================================================
    with tab7:
        st.markdown("### 🎯 Data-Driven Food Redistribution Recommendations")
        st.markdown("> **Operational Insight:** Identifies unfulfilled surplus items expiring within critical windows and matches them to suitable nearby receivers (NGOs/Shelters) by city and historical activity.")
        
        p_filter = st.selectbox("Filter Priority Level", ["All Priorities", "High Priority (Urgent Action)", "High Priority", "Medium Priority", "Normal / Available"])
        
        recs_df = get_redistribution_recommendations(df, limit=30)
        
        if not recs_df.empty:
            if p_filter != "All Priorities":
                recs_df = recs_df[recs_df["Priority"] == p_filter]
                
            st.write(f"Showing **{len(recs_df)} actionable allocations**:")
            
            for idx, r in recs_df.iterrows():
                priority_color = "urgent" if "High Priority (Urgent" in r["Priority"] else ("medium" if "High" in r["Priority"] else "resolved")
                with st.expander(f"📦 Item #{r['Food_ID']}: {r['Food_Name']} ({r['Quantity']} units) in {r['City']} ➔ {r['Recommended_Receiver']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Donor Provider:** {r['Provider']}")
                    c1.write(f"**Shelf Life:** {r['Shelf_Life_Status']}")
                    c2.write(f"**Suggested Receiver:** {r['Recommended_Receiver']}")
                    c2.write(f"**Organization Type:** {r['Receiver_Type']}")
                    c3.write(f"**Match Quality:** {r['Match_Confidence']}")
                    c3.write(f"**Receiver Contact:** {r['Receiver_Contact']}")
                    st.info(f"💡 **AI Dispatch Rationale:** {r['AI_Rationale']}")
                    
            st.markdown("---")
            st.download_button(
                label="📥 Export Redistribution Dispatch Manifest (CSV)",
                data=recs_df.to_csv(index=False).encode('utf-8'),
                file_name=f"redistribution_manifest_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.success("🎉 No critical unclaimed food items require urgent redistribution at this time!")

    # =========================================================
    # TAB 8: ADVANCED SQL INSIGHTS
    # =========================================================
    with tab8:
        st.markdown("### 🔍 Advanced SQL Insights & Query Workbench")
        st.caption("Execute predefined complex analytical queries or run custom read-only SQL queries.")

        selected_q_name = st.selectbox(
            "Select Predefined Analytical Query",
            list(PREDEFINED_QUERIES.keys())
        )
        
        q_info = PREDEFINED_QUERIES[selected_q_name]
        st.info(f"💡 **Description:** {q_info['description']}")
        
        with st.expander("View SQL Code", expanded=False):
            st.code(q_info["sql"], language="sql")
            
        if is_db_connected:
            try:
                sql_res = run_query(q_info["sql"])
                st.dataframe(sql_res, use_container_width=True)
            except Exception as e:
                st.error(f"Error executing query: {str(e)}")
        else:
            st.warning("⚠️ Live SQL execution is disabled because PostgreSQL is offline. Local CSV dataset analytics are active across other tabs.")

        st.markdown("---")
        st.markdown("#### ⚡ Safe Read-Only SQL Query Runner")
        custom_sql = st.text_area(
            "Enter custom SELECT query (Safe read-only execution only)",
            value="SELECT Location, Food_Type, SUM(Quantity) AS Total_Units FROM food_listings_data GROUP BY Location, Food_Type ORDER BY Total_Units DESC LIMIT 10;",
            height=100
        )
        
        if st.button("Run Query 🚀"):
            if is_db_connected:
                try:
                    custom_res = run_query(custom_sql)
                    st.success(f"Returned {len(custom_res)} rows successfully.")
                    st.dataframe(custom_res, use_container_width=True)
                except Exception as e:
                    st.error(f"Execution Error: {str(e)}")
            else:
                st.error("PostgreSQL connection is offline. Please verify PostgreSQL is running and check your .env configuration.")
