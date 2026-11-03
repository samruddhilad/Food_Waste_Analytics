"""
Database setup and migration utility for Food Waste Management Dashboard.
Initializes the PostgreSQL database schema, imports the dataset, and verifies table counts.
Safe to rerun: will not overwrite or duplicate existing records.
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import pandas as pd
from dotenv import load_dotenv

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment configuration
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

def get_config():
    """Retrieve database parameters with safe defaults."""
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
    }

def print_banner():
    print("=" * 65)
    print("🍽️  Food Waste Management Dashboard - PostgreSQL Setup Utility")
    print("=" * 65)

def ensure_database_exists(config: dict) -> bool:
    """
    Checks if target database exists; attempts automatic creation via maintenance db if missing.
    """
    target_db = config["database"]
    print(f"\n🔍 [1/5] Verifying PostgreSQL database '{target_db}'...")

    # First attempt direct connection to target DB
    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            dbname=target_db,
            connect_timeout=5
        )
        conn.close()
        print(f"   ✅ Database '{target_db}' exists and is accessible.")
        return True
    except psycopg2.OperationalError as e:
        err_msg = str(e).strip()
        if f'database "{target_db}" does not exist' not in err_msg and "does not exist" not in err_msg:
            # Re-raise server offline or auth errors
            raise e

    # Target database does not exist - attempt creation via 'postgres' maintenance DB
    print(f"   ℹ️  Database '{target_db}' not found. Attempting automatic creation via maintenance DB 'postgres'...")
    try:
        m_conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            dbname="postgres",
            connect_timeout=5
        )
        m_conn.autocommit = True
        with m_conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
        m_conn.close()
        print(f"   ✅ Successfully created database '{target_db}'.")
        return True
    except Exception as e:
        print(f"   ❌ Could not automatically create database: {e}")
        print("\n   👉 MANUAL STEP REQUIRED IN pgAdmin 4:")
        print("      1. Open pgAdmin 4 and connect to your PostgreSQL server.")
        print("      2. Right-click 'Databases' -> 'Create' -> 'Database...'.")
        print(f"      3. Enter Database name: {target_db}")
        print("      4. Click 'Save', then re-run this setup script.")
        return False

def apply_schema(config: dict, schema_path: Path):
    """Executes schema DDL script against target database."""
    print(f"\n📐 [2/5] Initializing database schema from {schema_path.name}...")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        dbname=config["database"]
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        print("   ✅ Schema tables and indexes verified/created successfully.")
    finally:
        conn.close()

def import_datasets(config: dict, dataset_dir: Path):
    """
    Imports all 4 datasets with proper foreign key order and ON CONFLICT handling.
    """
    print("\n📦 [3/5] Importing dataset records into PostgreSQL...")
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        dbname=config["database"]
    )
    conn.autocommit = False

    try:
        cur = conn.cursor()

        # 1. Providers
        p_path = dataset_dir / "providers_data.csv"
        if p_path.exists():
            p_df = pd.read_csv(p_path)
            p_records = [
                (
                    int(row["Provider_ID"]),
                    str(row["Name"]),
                    str(row["Type"]) if pd.notna(row["Type"]) else None,
                    str(row["Address"]) if pd.notna(row["Address"]) else None,
                    str(row["City"]) if pd.notna(row["City"]) else None,
                    str(row["Contact"]) if pd.notna(row["Contact"]) else None,
                    str(row.get("Country", "India")) if pd.notna(row.get("Country")) else "India"
                )
                for _, row in p_df.iterrows()
            ]
            execute_values(
                cur,
                """
                INSERT INTO providers_data (provider_id, name, type, address, city, contact, country)
                VALUES %s
                ON CONFLICT (provider_id) DO NOTHING;
                """,
                p_records
            )
            print(f"   ✅ Providers data processed: {len(p_records):,} records.")

        # 2. Receivers
        r_path = dataset_dir / "receivers_data.csv"
        if r_path.exists():
            r_df = pd.read_csv(r_path)
            r_records = [
                (
                    int(row["Receiver_ID"]),
                    str(row["Name"]),
                    str(row["Type"]) if pd.notna(row["Type"]) else None,
                    str(row["City"]) if pd.notna(row["City"]) else None,
                    str(row["Contact"]) if pd.notna(row["Contact"]) else None,
                    str(row.get("Country", "India")) if pd.notna(row.get("Country")) else "India"
                )
                for _, row in r_df.iterrows()
            ]
            execute_values(
                cur,
                """
                INSERT INTO receivers_data (receiver_id, name, type, city, contact, country)
                VALUES %s
                ON CONFLICT (receiver_id) DO NOTHING;
                """,
                r_records
            )
            print(f"   ✅ Receivers data processed: {len(r_records):,} records.")

        # 3. Food Listings
        f_path = dataset_dir / "food_listings_data.csv"
        if f_path.exists():
            f_df = pd.read_csv(f_path)
            f_records = []
            for _, row in f_df.iterrows():
                exp_ts = pd.to_datetime(row["Expiry_Date"], format="mixed", errors="coerce")
                exp_val = exp_ts.date() if pd.notna(exp_ts) else None
                f_records.append((
                    int(row["Food_ID"]),
                    str(row["Food_Name"]),
                    int(row["Quantity"]) if pd.notna(row["Quantity"]) else 0,
                    exp_val,
                    int(row["Provider_ID"]) if pd.notna(row["Provider_ID"]) else None,
                    str(row["Provider_Type"]) if pd.notna(row["Provider_Type"]) else None,
                    str(row["Location"]) if pd.notna(row["Location"]) else None,
                    str(row["Food_Type"]) if pd.notna(row["Food_Type"]) else None,
                    str(row["Meal_Type"]) if pd.notna(row["Meal_Type"]) else None,
                    str(row.get("Country", "India")) if pd.notna(row.get("Country")) else "India"
                ))
            execute_values(
                cur,
                """
                INSERT INTO food_listings_data (food_id, food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type, country)
                VALUES %s
                ON CONFLICT (food_id) DO NOTHING;
                """,
                f_records
            )
            print(f"   ✅ Food listings processed: {len(f_records):,} records.")

        # 4. Claims
        c_path = dataset_dir / "claims_data.csv"
        if c_path.exists():
            c_df = pd.read_csv(c_path)
            c_records = []
            for _, row in c_df.iterrows():
                ts = pd.to_datetime(row["Timestamp"], format="mixed", errors="coerce")
                ts_val = ts.to_pydatetime() if pd.notna(ts) else None
                c_records.append((
                    int(row["Claim_ID"]),
                    int(row["Food_ID"]) if pd.notna(row["Food_ID"]) else None,
                    int(row["Receiver_ID"]) if pd.notna(row["Receiver_ID"]) else None,
                    str(row["Status"]) if pd.notna(row["Status"]) else "Pending",
                    ts_val
                ))
            execute_values(
                cur,
                """
                INSERT INTO claims_data (claim_id, food_id, receiver_id, status, timestamp)
                VALUES %s
                ON CONFLICT (claim_id) DO NOTHING;
                """,
                c_records
            )
            print(f"   ✅ Claims data processed: {len(c_records):,} records.")

        # Sync serial sequences
        cur.execute("SELECT setval(pg_get_serial_sequence('providers_data', 'provider_id'), COALESCE((SELECT MAX(provider_id) FROM providers_data), 1));")
        cur.execute("SELECT setval(pg_get_serial_sequence('receivers_data', 'receiver_id'), COALESCE((SELECT MAX(receiver_id) FROM receivers_data), 1));")
        cur.execute("SELECT setval(pg_get_serial_sequence('food_listings_data', 'food_id'), COALESCE((SELECT MAX(food_id) FROM food_listings_data), 1));")
        cur.execute("SELECT setval(pg_get_serial_sequence('claims_data', 'claim_id'), COALESCE((SELECT MAX(claim_id) FROM claims_data), 1));")

        conn.commit()
        print("   ✅ Data transaction committed successfully.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def verify_installation(config: dict):
    """Queries live record counts and executes a validation query."""
    print("\n📊 [4/5] Verifying database tables and live record counts...")
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        dbname=config["database"]
    )
    counts = {}
    try:
        with conn.cursor() as cur:
            tables = ["providers_data", "receivers_data", "food_listings_data", "claims_data"]
            for tbl in tables:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(tbl)))
                counts[tbl] = cur.fetchone()[0]

            # Execute sample analytics query
            cur.execute("""
                SELECT p.type, SUM(f.quantity) as total_qty
                FROM food_listings_data f
                JOIN providers_data p ON f.provider_id = p.provider_id
                GROUP BY p.type
                ORDER BY total_qty DESC
                LIMIT 3;
            """)
            sample_results = cur.fetchall()
    finally:
        conn.close()

    print("   Live Row Counts:")
    for tbl, cnt in counts.items():
        print(f"     • {tbl:<20}: {cnt:>6,} rows")

    print("\n   Sample Analytical Query (Top Provider Types by Quantity):")
    for row in sample_results:
        print(f"     • {row[0]:<20}: {row[1]:>6,} units")

    return counts

def main():
    print_banner()
    config = get_config()
    print(f"\nTarget Server: {config['host']}:{config['port']}")
    print(f"Target Database: {config['database']}")
    print(f"Target User: {config['user']}")

    schema_file = PROJECT_ROOT / "database" / "postgres_schema.sql"
    dataset_folder = PROJECT_ROOT / "dataset"

    try:
        ok = ensure_database_exists(config)
        if not ok:
            sys.exit(1)

        apply_schema(config, schema_file)
        import_datasets(config, dataset_folder)
        counts = verify_installation(config)

        print("\n" + "=" * 65)
        print("🎉 [5/5] PostgreSQL Migration Complete & Verified!")
        print("=" * 65)
        print("You can now start your dashboard with:")
        print("   python -m streamlit run app.py\n")

    except psycopg2.OperationalError as e:
        err = str(e).strip()
        print("\n❌ Database Connection Error:")
        if "Connection refused" in err or "timeout expired" in err or "could not connect to server" in err:
            print(f"   Cannot connect to PostgreSQL server at {config['host']}:{config['port']}.")
            print("   👉 Please ensure your PostgreSQL service is started and listening.")
        elif "password authentication failed" in err:
            print(f"   Password authentication failed for user '{config['user']}'.")
            print("   👉 Please check DB_USER and DB_PASSWORD in your .env file.")
        else:
            print(f"   {err}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
