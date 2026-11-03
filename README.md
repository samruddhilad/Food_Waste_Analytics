# 🍽️ Intelligent Food Waste Analytics & Redistribution System

An intelligent, multi-tier data analytics and AI-powered food redistribution dashboard built using **Python, Streamlit, PostgreSQL, pgAdmin 4, Pandas, Plotly, LangChain, and LangGraph**.

---

## 📌 Project Architecture

```
PostgreSQL Database (pgAdmin 4 / food_waste_db)
      ↓
Python + psycopg2-binary (database/connection.py, database/queries.py)
      ↓
Data Integration & Cleaning (data/processing.py)
      ↓
Analytics Engine (analytics/analytics.py)
      ↓
LangChain Tools (ai/langchain_tools.py)
      ↓
LangGraph Multi-Step StateGraph (ai/langgraph_workflow.py)
      ↓
Interactive UI / Recommendations / Charts (ui/dashboard.py, ui/charts.py, app.py)
```

---

## 🗂️ Dataset & Entity Relationships

The system connects four relational database tables:

1. **`food_listings_data`**: `Food_ID`, `Food_Name`, `Quantity`, `Expiry_Date`, `Provider_ID`, `Provider_Type`, `Location`, `Food_Type`, `Meal_Type`
2. **`providers_data`**: `Provider_ID`, `Name`, `Type`, `Address`, `City`, `Contact`
3. **`receivers_data`**: `Receiver_ID`, `Name`, `Type`, `City`, `Contact`
4. **`claims_data`**: `Claim_ID`, `Food_ID`, `Receiver_ID`, `Status`, `Timestamp`

### Integration Pipeline (`data/processing.py`):
```
food_listings_data
        + (LEFT JOIN on Provider_ID)
providers_data
        ↓
food_provider_data
        + (LEFT JOIN on Food_ID - preserves unclaimed listings!)
claims_data
        ↓
food_claim_data
        + (LEFT JOIN on Receiver_ID)
receivers_data
        ↓
final_integrated_dataset
```

---

## 🧠 LangChain & LangGraph AI Layer

### 1. LangChain Tool Layer (`ai/langchain_tools.py`)
Provides safe, read-only analytical tools:
- `get_food_statistics`: Overall food inventory, dietary distributions, and potential meal counts.
- `get_unclaimed_food`: Unclaimed surplus food volume and regional breakdown.
- `get_expiring_food`: Urgent food items expiring within 48 hours or approaching expiry.
- `get_provider_statistics`: Donor leaderboard, business categories, and donation volumes.
- `get_receiver_statistics`: Top NGOs, shelters, and claim frequencies.
- `get_claims_statistics`: Completed, pending, and cancelled claims breakdown.
- `get_city_food_waste_summary`: City-by-city food volume and waste metrics.
- `get_redistribution_candidates`: Algorithmic priority food-to-receiver matches.

### 2. LangGraph Workflow (`ai/langgraph_workflow.py`)
Implements a 5-node StateGraph for multi-step reasoning:

```
START ➔ [Intent Detector] ➔ [Data Retriever] ➔ [Data Analyzer] ➔ [Recommendation Engine] ➔ [Response Generator] ➔ END
```

- **Supported Intents**: `food_analysis`, `provider_analysis`, `receiver_analysis`, `claim_analysis`, `expiry_analysis`, `redistribution_recommendation`, `city_waste_analysis`, `general_summary`.
- **LLM Support**: Configurable with **Google Gemini** (`ChatGoogleGenerativeAI`) or **OpenAI** (`ChatOpenAI`).
- **Deterministic Fallback**: If no API key is set, the built-in deterministic NLP engine generates rich, formatted statistical answers without failing.

---

## 🎯 Smart Redistribution Recommendations

For food that is **unclaimed**, **approaching expiry**, and **available in significant volume**, the system matches items with local registered receivers (NGOs and shelters) in the same city.

> *Note: Recommendations are clearly labeled as AI/data-driven suggestions to assist logistics teams.*

---

## 🚀 Step-by-Step Setup Instructions

### 1. Database Setup with pgAdmin 4 & PostgreSQL

You can initialize the database using either the automated setup script or via pgAdmin 4.

#### Option A: Automated Setup (Recommended)
1. Ensure your PostgreSQL service is running.
2. In your `.env` file, configure your PostgreSQL credentials:
   ```ini
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   DB_NAME=food_waste_db
   ```
3. Run the automated database setup utility:
   ```bash
   python setup_postgres.py
   ```
   *This utility automatically verifies connectivity, creates `food_waste_db` if needed, applies `database/postgres_schema.sql`, imports all 4 datasets (1,000 records each), updates sequences, and verifies table counts.*

#### Option B: Manual Setup via pgAdmin 4
1. Open **pgAdmin 4**.
2. Connect to your local PostgreSQL server.
3. Right-click **Databases** ➔ **Create** ➔ **Database...**.
4. Name the database **`food_waste_db`** and click **Save**.
5. Select `food_waste_db`, open the **Query Tool** (Tools ➔ Query Tool).
6. Open and execute `database/postgres_schema.sql` (click Execute/F5).
7. Open and execute `database/postgres_data.sql` to import the records.

### 2. Configure Environment (`.env`)
Create or edit `.env` in the root directory:

```ini
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_NAME=food_waste_db

# Optional: Google Gemini API Key (Recommended for AI Assistant)
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Create & Activate Virtual Environment

**Windows (PowerShell / CMD):**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Streamlit Dashboard
```bash
python -m streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## 📊 Dashboard Tabs

1. **📊 Overview**: Global KPI cards, trend chart, status donut, and geographic interactive map.
2. **🍱 Food Analytics**: Dietary food types, meal categories, city-wise inventory, and detailed table.
3. **🏪 Provider Analytics**: Top donors leaderboard, provider types, and donation volumes.
4. **🤝 Receiver Analytics**: Top NGOs/shelters, claim counts, and receiver organization types.
5. **📈 Claims Analytics**: Claim status distribution, completion rates, and transaction logs.
6. **🤖 AI Assistant**: LangChain & LangGraph powered conversational assistant with suggestion chips.
7. **🎯 Smart Recommendations**: Algorithmic & AI matching of urgent surplus food to local receivers with CSV export.
8. **🔍 SQL Insights**: Interactive 18 predefined analytical queries and safe read-only SQL workbench.

---

## 🔒 Security Measures
- Credentials and API keys are stored in `.env` (git-ignored).
- Passwords and secret keys are never displayed in the UI.
- All AI and custom query inputs enforce strict **read-only SQL rules**, completely blocking `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, and `TRUNCATE`.
