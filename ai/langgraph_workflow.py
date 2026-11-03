from typing import TypedDict, Optional, Dict, Any, List
import pandas as pd
from langgraph.graph import StateGraph, START, END

from ai.llm_factory import get_llm, get_configured_llm_info
from ai.prompts import SYSTEM_PROMPT, INTENT_DETECTION_PROMPT, RESPONSE_GENERATION_PROMPT
from ai.langchain_tools import (
    get_food_statistics,
    get_unclaimed_food,
    get_expiring_food,
    get_provider_statistics,
    get_receiver_statistics,
    get_claims_statistics,
    get_city_food_waste_summary,
    get_redistribution_candidates,
    refresh_tool_dataset
)

# 1. State Definition
class AgentState(TypedDict):
    question: str
    intent: str
    retrieved_data: Dict[str, Any]
    analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    final_response: str
    error: Optional[str]
    llm_provider: str
    custom_key: Optional[str]
    provider_choice: Optional[str]

# 2. Node 1: Intent Detection
def intent_detector_node(state: AgentState) -> Dict[str, Any]:
    question = state.get("question", "").lower()
    llm = get_llm(custom_key=state.get("custom_key"), provider_choice=state.get("provider_choice"))
    
    # Try LLM intent detection if available
    if llm is not None:
        try:
            prompt = INTENT_DETECTION_PROMPT.format(question=question)
            res = llm.invoke([{"role": "system", "content": "You are a concise classifier."}, {"role": "user", "content": prompt}])
            detected = res.content.strip().lower()
            valid_intents = [
                "food_analysis", "provider_analysis", "receiver_analysis",
                "claim_analysis", "expiry_analysis", "redistribution_recommendation",
                "city_waste_analysis", "general_summary"
            ]
            for v in valid_intents:
                if v in detected:
                    return {"intent": v}
        except Exception:
            pass

    # Deterministic Rule-Based Intent Classifier Fallback
    if any(w in question for w in ["redistribut", "priorit", "where to send", "dispatch", "suitable receiver", "allocate"]):
        intent = "redistribution_recommendation"
    elif any(w in question for w in ["expir", "spoil", "shelf life", "fresh", "bad"]):
        intent = "expiry_analysis"
    elif any(w in question for w in ["unclaim", "waste", "loss", "leftover", "surplus"]):
        if any(w in question for w in ["city", "where", "location"]):
            intent = "city_waste_analysis"
        else:
            intent = "food_analysis"
    elif any(w in question for w in ["city", "cities", "location", "geographic", "mumbai", "delhi", "bangalore"]):
        intent = "city_waste_analysis"
    elif any(w in question for w in ["provider", "donor", "contribut", "supermarket", "restaurant", "store"]):
        intent = "provider_analysis"
    elif any(w in question for w in ["receiver", "ngo", "shelter", "charity", "beneficiar", "claimant"]):
        intent = "receiver_analysis"
    elif any(w in question for w in ["claim", "pending", "completed", "cancelled", "status"]):
        intent = "claim_analysis"
    elif any(w in question for w in ["summary", "overview", "situation", "overall", "health", "metrics"]):
        intent = "general_summary"
    else:
        intent = "food_analysis"

    return {"intent": intent}

# 3. Node 2: Data Retrieval
def data_retriever_node(state: AgentState) -> Dict[str, Any]:
    intent = state.get("intent", "general_summary")
    retrieved = {}
    
    try:
        if intent == "food_analysis":
            retrieved["food_stats"] = get_food_statistics.invoke({})
            retrieved["unclaimed"] = get_unclaimed_food.invoke({})
        elif intent == "provider_analysis":
            retrieved["providers"] = get_provider_statistics.invoke({})
        elif intent == "receiver_analysis":
            retrieved["receivers"] = get_receiver_statistics.invoke({})
        elif intent == "claim_analysis":
            retrieved["claims"] = get_claims_statistics.invoke({})
        elif intent == "expiry_analysis":
            retrieved["expiry"] = get_expiring_food.invoke({})
        elif intent == "city_waste_analysis":
            retrieved["city_waste"] = get_city_food_waste_summary.invoke({})
            retrieved["unclaimed"] = get_unclaimed_food.invoke({})
        elif intent == "redistribution_recommendation":
            retrieved["redistribution"] = get_redistribution_candidates.invoke({})
            retrieved["expiry"] = get_expiring_food.invoke({})
        else: # general_summary
            retrieved["food_stats"] = get_food_statistics.invoke({})
            retrieved["claims"] = get_claims_statistics.invoke({})
            retrieved["expiry"] = get_expiring_food.invoke({})
            retrieved["providers"] = get_provider_statistics.invoke({})
    except Exception as e:
        return {"retrieved_data": {}, "error": f"Error retrieving data: {str(e)}"}

    return {"retrieved_data": retrieved}

# 4. Node 3: Data Analysis
def data_analyzer_node(state: AgentState) -> Dict[str, Any]:
    intent = state.get("intent", "general_summary")
    retrieved = state.get("retrieved_data", {})
    analysis = {}

    if intent == "food_analysis":
        fs = retrieved.get("food_stats", {})
        unc = retrieved.get("unclaimed", {})
        analysis["summary"] = f"Total of {fs.get('total_food_quantity', 0)} food units across {fs.get('total_food_listings', 0)} listings. {unc.get('total_unclaimed_quantity', 0)} units remain unclaimed."
    
    elif intent == "provider_analysis":
        pv = retrieved.get("providers", {})
        top_list = pv.get("top_providers", [])
        top_name = top_list[0].get("Provider_Name") if top_list else "Unknown"
        top_qty = top_list[0].get("Total_Donated_Qty") if top_list else 0
        analysis["summary"] = f"{pv.get('total_registered_providers', 0)} active food providers. Top donor is '{top_name}' with {top_qty} units donated."

    elif intent == "receiver_analysis":
        rc = retrieved.get("receivers", {})
        top_list = rc.get("top_receivers", [])
        top_name = top_list[0].get("Receiver_Name") if top_list else "Unknown"
        top_claims = top_list[0].get("Total_Claims") if top_list else 0
        analysis["summary"] = f"{rc.get('total_registered_receivers', 0)} registered receivers. Most active claimant is '{top_name}' with {top_claims} claims."

    elif intent == "expiry_analysis":
        exp = retrieved.get("expiry", {})
        analysis["summary"] = f"{exp.get('critical_expiring_count', 0)} listings ({exp.get('critical_expiring_quantity', 0)} units) are critically expiring within 48 hours."

    elif intent == "city_waste_analysis":
        cw = retrieved.get("city_waste", {})
        top_city = cw.get("top_city_highest_waste", {})
        city_name = top_city.get("City", "Unknown")
        waste_qty = top_city.get("Unclaimed_Quantity", 0)
        analysis["summary"] = f"Highest surplus/unclaimed waste is concentrated in '{city_name}' with {waste_qty} units unclaimed."

    elif intent == "redistribution_recommendation":
        red = retrieved.get("redistribution", {})
        count = red.get("recommendations_count", 0)
        analysis["summary"] = f"Generated {count} high-priority food-to-receiver redistribution matches based on urgency, shelf-life, and city proximity."

    else:
        analysis["summary"] = "Integrated multi-table analytics evaluated across listings, claims, providers, and receivers."

    return {"analysis": analysis}

# 5. Node 4: Recommendation Generation
def recommendation_generator_node(state: AgentState) -> Dict[str, Any]:
    intent = state.get("intent", "")
    retrieved = state.get("retrieved_data", {})
    recs = []

    if intent in ["redistribution_recommendation", "expiry_analysis", "general_summary", "food_analysis"]:
        # Pull priority recommendations
        candidates = get_redistribution_candidates.invoke({}).get("priority_redistributions", [])
        recs = candidates[:5]

    return {"recommendations": recs}

# 6. Node 5: Response Generation (LLM or Rule-Engine)
def response_generator_node(state: AgentState) -> Dict[str, Any]:
    question = state.get("question", "")
    intent = state.get("intent", "")
    data = state.get("retrieved_data", {})
    analysis = state.get("analysis", {})
    recs = state.get("recommendations", [])
    
    llm = get_llm(custom_key=state.get("custom_key"), provider_choice=state.get("provider_choice"))
    provider_name, is_llm_active = get_configured_llm_info(custom_key=state.get("custom_key"), provider_choice=state.get("provider_choice"))

    # If LLM is available, generate dynamic response with LangChain
    if llm is not None:
        try:
            prompt_text = RESPONSE_GENERATION_PROMPT.format(
                question=question,
                intent=intent,
                data=str(data),
                analysis=str(analysis),
                recommendations=str(recs)
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text}
            ]
            res = llm.invoke(messages)
            return {
                "final_response": res.content,
                "llm_provider": provider_name
            }
        except Exception as e:
            # Fallback to deterministic formatter below
            pass

    # Deterministic Structured Markdown Generator (No API Key Required)
    lines = []
    lines.append(f"### 🍽️ AI Analysis Report: `{intent.replace('_', ' ').title()}`\n")
    lines.append(f"**Key Finding:** {analysis.get('summary', 'Analysis completed.')}\n")
    
    if intent == "food_analysis":
        fs = data.get("food_stats", {})
        lines.append("#### 📊 Food Volume Breakdown:")
        lines.append(f"- **Total Listed Food:** {fs.get('total_food_quantity', 0):,} units ({fs.get('total_food_listings', 0)} listings)")
        lines.append(f"- **Unclaimed Surplus:** {fs.get('unclaimed_quantity', 0):,} units")
        lines.append(f"- **Critical Expiry (<48h):** {fs.get('critical_expiry_quantity', 0):,} units")
        lines.append(f"- **Potential Meal Equivalents:** {fs.get('potential_meals', 0):,} meals\n")
        
        types = fs.get("food_dietary_types", [])
        if types:
            lines.append("#### 🥗 Dietary Distribution:")
            for t in types:
                lines.append(f"- **{t.get('Food_Type', 'Type')}:** {t.get('Total_Quantity', 0):,} units ({t.get('Listing_Count', 0)} listings)")

    elif intent == "provider_analysis":
        pv = data.get("providers", {})
        lines.append(f"**Total Registered Providers:** {pv.get('total_registered_providers', 0)}")
        lines.append("\n#### 🏪 Top Contributing Providers:")
        for p in pv.get("top_providers", [])[:5]:
            lines.append(f"1. **{p.get('Provider_Name')}** ({p.get('Provider_Business_Type')}, {p.get('City')}) — **{p.get('Total_Donated_Qty', 0):,} units** donated ({p.get('Completed_Claims', 0)} completed claims)")

    elif intent == "receiver_analysis":
        rc = data.get("receivers", {})
        lines.append(f"**Total Registered Receivers:** {rc.get('total_registered_receivers', 0)}")
        lines.append("\n#### 🤝 Most Active Receivers (NGOs & Shelters):")
        for r in rc.get("top_receivers", [])[:5]:
            lines.append(f"1. **{r.get('Receiver_Name')}** ({r.get('Receiver_Organization_Type')}, {r.get('Receiver_City')}) — **{r.get('Total_Claims', 0)} total claims** ({r.get('Total_Quantity_Claimed', 0):,} units received)")

    elif intent == "expiry_analysis":
        exp = data.get("expiry", {})
        lines.append(f"- **Critically Expiring (<48 hrs):** {exp.get('critical_expiring_count', 0)} items ({exp.get('critical_expiring_quantity', 0):,} units)")
        lines.append(f"- **Approaching Expiry (3-7 days):** {exp.get('approaching_expiry_count', 0)} items ({exp.get('approaching_expiry_quantity', 0):,} units)")
        lines.append(f"- **Expired Items (To Compost):** {exp.get('expired_items_count', 0)} items\n")
        
        urgent = exp.get("urgent_critical_items", [])
        if urgent:
            lines.append("#### ⚠️ Immediate Action Required on Items:")
            for u in urgent[:4]:
                lines.append(f"- **Item #{u.get('Food_ID')} ({u.get('Food_Name')}):** {u.get('Quantity')} units in {u.get('Location')} (Donor: {u.get('Provider_Name')})")

    elif intent == "city_waste_analysis":
        cw = data.get("city_waste", {})
        lines.append("#### 📍 City-wise Food Availability & Unclaimed Food:")
        for c in cw.get("top_cities_by_food_volume", [])[:5]:
            lines.append(f"- **{c.get('City')}:** {c.get('Total_Quantity', 0):,} total units | **{c.get('Unclaimed_Quantity', 0):,} unclaimed** ({c.get('Total_Listings', 0)} listings)")

    elif intent == "claim_analysis":
        cl = data.get("claims", {})
        lines.append("#### 📈 Claim Fulfillment Statistics:")
        lines.append(f"- **Total Claims Processed:** {cl.get('total_claims', 0):,}")
        lines.append(f"- **Successfully Completed:** {cl.get('completed_claims', 0):,}")
        lines.append(f"- **Pending Action:** {cl.get('pending_claims', 0):,}")
        lines.append(f"- **Cancelled Claims:** {cl.get('cancelled_claims', 0):,}")
        lines.append(f"- **Claim Fulfillment Rate:** {cl.get('claim_fulfillment_rate_pct', 0)}%")

    # Add Actionable AI Recommendations if available
    if recs:
        lines.append("\n---")
        lines.append("### 🎯 AI-Recommended Redistribution Actions:")
        lines.append("> *Note: These are AI data-driven matching suggestions based on shelf-life urgency and receiver proximity.*")
        for idx, r in enumerate(recs[:3], 1):
            lines.append(f"{idx}. **Allocate {r.get('Food_Name')} ({r.get('Quantity')} units)** in `{r.get('City')}`")
            lines.append(f"   - **Suggested Receiver:** {r.get('Recommended_Receiver')} ({r.get('Receiver_Type')})")
            lines.append(f"   - **Match Confidence:** {r.get('Match_Confidence')}")
            lines.append(f"   - **Rationale:** {r.get('AI_Rationale')}")

    if not is_llm_active:
        lines.append("\n---")
        lines.append("💡 *Tip: Add a `GOOGLE_API_KEY` (Gemini) or `OPENAI_API_KEY` in `.env` or the sidebar to unlock conversational generative responses.*")

    return {
        "final_response": "\n".join(lines),
        "llm_provider": provider_name
    }

# 7. Compile LangGraph StateGraph
def build_food_waste_graph():
    """Builds and compiles the multi-step LangGraph StateGraph."""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("intent_detector", intent_detector_node)
    graph.add_node("data_retriever", data_retriever_node)
    graph.add_node("data_analyzer", data_analyzer_node)
    graph.add_node("recommendation_generator", recommendation_generator_node)
    graph.add_node("response_generator", response_generator_node)
    
    # Define linear flow
    graph.add_edge(START, "intent_detector")
    graph.add_edge("intent_detector", "data_retriever")
    graph.add_edge("data_retriever", "data_analyzer")
    graph.add_edge("data_analyzer", "recommendation_generator")
    graph.add_edge("recommendation_generator", "response_generator")
    graph.add_edge("response_generator", END)
    
    return graph.compile()

# Global compiled graph instance
_compiled_graph = None

def run_food_waste_workflow(
    question: str,
    df: pd.DataFrame = None,
    custom_key: Optional[str] = None,
    provider_choice: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes the multi-step LangGraph workflow for a given user question.
    """
    global _compiled_graph
    if df is not None:
        refresh_tool_dataset(df)
        
    if _compiled_graph is None:
        _compiled_graph = build_food_waste_graph()

    initial_state: AgentState = {
        "question": question,
        "intent": "",
        "retrieved_data": {},
        "analysis": {},
        "recommendations": [],
        "final_response": "",
        "error": None,
        "llm_provider": "",
        "custom_key": custom_key,
        "provider_choice": provider_choice
    }

    result = _compiled_graph.invoke(initial_state)
    return result
