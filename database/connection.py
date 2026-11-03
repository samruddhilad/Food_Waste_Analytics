import os
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Mapping of lowercase column names returned by PostgreSQL to canonical casing
# required by downstream analytics, charts, and data integration routines.
COLUMN_CASE_MAP: Dict[str, str] = {
    # providers_data
    "provider_id": "Provider_ID",
    "name": "Name",
    "type": "Type",
    "address": "Address",
    "city": "City",
    "contact": "Contact",
    "country": "Country",
    # receivers_data
    "receiver_id": "Receiver_ID",
    # food_listings_data
    "food_id": "Food_ID",
    "food_name": "Food_Name",
    "quantity": "Quantity",
    "expiry_date": "Expiry_Date",
    "provider_type": "Provider_Type",
    "location": "Location",
    "food_type": "Food_Type",
    "meal_type": "Meal_Type",
    # claims_data
    "claim_id": "Claim_ID",
    "status": "Status",
    "timestamp": "Timestamp",
}

def get_db_config() -> Dict[str, Any]:
    """
    Retrieve PostgreSQL connection parameters from environment variables with safe defaults.
    Never exposes passwords in logs or traces.
    """
    port_val = os.getenv("DB_PORT", "5432")
    try:
        port = int(port_val) if port_val and str(port_val).strip() else 5432
    except (ValueError, TypeError):
        port = 5432

    return {
        "host": os.getenv("DB_HOST", "localhost") or "localhost",
        "port": port,
        "user": os.getenv("DB_USER", "postgres") or "postgres",
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "food_waste_db") or "food_waste_db",
        "connect_timeout": 5,
    }

def get_safe_db_info() -> Dict[str, Any]:
    """Returns connection parameters without sensitive credentials."""
    config = get_db_config()
    return {
        "host": config["host"],
        "port": config["port"],
        "user": config["user"],
        "database": config["database"],
    }

def test_connection() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Tests the PostgreSQL database connection and queries the server version.
    Returns:
        tuple: (bool is_success, str message_or_version, dict safe_db_info)
    """
    config = get_db_config()
    safe_info = get_safe_db_info()

    conn = None
    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            dbname=config["database"],
            connect_timeout=config["connect_timeout"]
        )
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            ver_raw = cur.fetchone()[0]
            # Extract concise version e.g. "PostgreSQL 17.x"
            ver_match = re.search(r"PostgreSQL\s+[\d\.]+", ver_raw)
            version_str = ver_match.group(0) if ver_match else "PostgreSQL"
            
            # Quick check that expected tables exist
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('providers_data', 'receivers_data', 'food_listings_data', 'claims_data');
            """)
            found_tables = [row[0] for row in cur.fetchall()]
            
        conn.close()
        
        if len(found_tables) < 4:
            msg = f"Connected to {version_str}, but only {len(found_tables)}/4 tables found in '{config['database']}'. Please run 'python setup_postgres.py' to initialize schema and import data."
        else:
            msg = f"Connected to {version_str} (`{config['database']}`)"
            
        return True, msg, safe_info

    except psycopg2.OperationalError as err:
        err_msg = str(err).strip()
        safe_user = config["user"]
        safe_host = config["host"]
        safe_port = config["port"]
        safe_db = config["database"]

        if "Connection refused" in err_msg or "timeout expired" in err_msg or "could not connect to server" in err_msg:
            msg = (
                f"Cannot reach PostgreSQL server at {safe_host}:{safe_port}. "
                "Ensure PostgreSQL service is running and listening on port 5432."
            )
        elif "password authentication failed" in err_msg:
            msg = (
                f"Password authentication failed for user '{safe_user}'. "
                "Please check DB_PASSWORD and DB_USER in your .env file."
            )
        elif f'database "{safe_db}" does not exist' in err_msg or "does not exist" in err_msg:
            msg = (
                f"Database '{safe_db}' does not exist on PostgreSQL. "
                "Please create it in pgAdmin 4 or run 'python setup_postgres.py'."
            )
        else:
            # Clean error string (strip out any accidental credential reflection)
            cleaned = err_msg.replace(config["password"], "******") if config["password"] else err_msg
            msg = f"PostgreSQL connection error: {cleaned}"

        return False, msg, safe_info

    except Exception as e:
        err_str = str(e)
        if config["password"] and config["password"] in err_str:
            err_str = err_str.replace(config["password"], "******")
        return False, f"Unexpected error connecting to database: {err_str}", safe_info

def get_db_connection():
    """
    Creates and returns a raw PostgreSQL connection.
    Raises:
        ConnectionError with sanitized, actionable message on failure.
    """
    config = get_db_config()
    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            dbname=config["database"],
            connect_timeout=config["connect_timeout"]
        )
        return conn
    except psycopg2.OperationalError as err:
        err_msg = str(err).strip()
        safe_user = config["user"]
        safe_host = config["host"]
        safe_port = config["port"]
        safe_db = config["database"]

        if "Connection refused" in err_msg or "timeout expired" in err_msg or "could not connect to server" in err_msg:
            raise ConnectionError(
                f"PostgreSQL server is offline at {safe_host}:{safe_port}. "
                "Please ensure the PostgreSQL service is started."
            )
        elif "password authentication failed" in err_msg:
            raise ConnectionError(
                f"Authentication failed for PostgreSQL user '{safe_user}'. "
                "Please check DB_USER and DB_PASSWORD in your .env file."
            )
        elif f'database "{safe_db}" does not exist' in err_msg or "does not exist" in err_msg:
            raise ConnectionError(
                f"Database '{safe_db}' not found on PostgreSQL server. "
                "Please create it in pgAdmin 4 or run 'python setup_postgres.py'."
            )
        else:
            cleaned = err_msg.replace(config["password"], "******") if config["password"] else err_msg
            raise ConnectionError(f"PostgreSQL error: {cleaned}")
    except Exception as e:
        err_str = str(e)
        if config["password"] and config["password"] in err_str:
            err_str = err_str.replace(config["password"], "******")
        raise ConnectionError(f"Failed to connect to PostgreSQL: {err_str}")

def is_safe_readonly_query(query: str) -> bool:
    """
    Validates that a SQL query contains only read-only statements.
    Rejects destructive/modifying SQL keywords.
    """
    cleaned = re.sub(r"--.*?\n", " ", query)
    cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip().upper()

    # Block destructive keywords
    forbidden = [
        r"\bDROP\b", r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b",
        r"\bALTER\b", r"\bTRUNCATE\b", r"\bREPLACE\b", r"\bCREATE\b",
        r"\bGRANT\b", r"\bREVOKE\b", r"\bEXEC\b", r"\bEXECUTE\b",
        r"\bCOPY\b", r"\bVACUUM\b", r"\bREINDEX\b"
    ]
    for pattern in forbidden:
        if re.search(pattern, cleaned):
            return False

    # Must begin with SELECT, WITH, SHOW, DESCRIBE, or EXPLAIN
    if not (cleaned.startswith("SELECT") or cleaned.startswith("WITH") or
            cleaned.startswith("SHOW") or cleaned.startswith("DESCRIBE") or
            cleaned.startswith("DESC") or cleaned.startswith("EXPLAIN")):
        return False

    return True

def run_query(query: str, params=None) -> pd.DataFrame:
    """
    Executes a safe read-only SQL query against PostgreSQL and returns a pandas DataFrame.
    Gracefully handles connection errors and maps column names to canonical casing.
    """
    if not is_safe_readonly_query(query):
        raise ValueError("Security Alert: Only read-only SELECT/WITH/EXPLAIN queries are allowed. Destructive statements are blocked.")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)
            
            # Canonicalize column name casing for seamless integration with downstream analytics
            if not df.empty:
                df = df.rename(columns={col: COLUMN_CASE_MAP.get(str(col).lower(), col) for col in df.columns})
            elif cursor.description:
                cols = [COLUMN_CASE_MAP.get(str(desc[0]).lower(), desc[0]) for desc in cursor.description]
                df = pd.DataFrame(columns=cols)
            else:
                df = pd.DataFrame()
                
            return df
    except Exception as e:
        raise RuntimeError(f"Database query execution failed: {str(e)}")
    finally:
        if conn and not conn.closed:
            conn.close()
