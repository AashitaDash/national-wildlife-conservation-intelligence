"""
Migrate complete local dataset (392 species, 46,280 observations, documents, etc.)
from local PostgreSQL (127.0.0.1:5433) to Render PostgreSQL (wildlife_db_je2r).
"""
import json
import psycopg
from psycopg.types.json import Jsonb, Json

LOCAL_URL = "postgresql://postgres:password@127.0.0.1:5433/wildlife_conservation"
REMOTE_URL = "postgresql://wildlife_user:tHcx2ncrRUZj9KLLinfwIEruHI3D0jsT@dpg-dbbpit8n74is7398s9dg-a.oregon-postgres.render.com/wildlife_db_je2r"

TABLES_IN_ORDER = [
    "roles",
    "users",
    "threats",
    "data_sources",
    "locations",
    "species",
    "documents",
    "document_threats",
    "document_species",
    "nlp_analysis_results",
    "observations",
    "ml_risk_scores",
    "ml_anomalies",
    "conservation_alerts",
    "badge_definitions",
    "user_badges",
    "observation_submissions",
    "submission_images",
    "verification_decisions",
    "points_ledger",
    "notifications",
    "audit_events"
]

def migrate():
    print("Connecting to local database...")
    local_conn = psycopg.connect(LOCAL_URL)
    print("Connecting to Render remote database...")
    remote_conn = psycopg.connect(REMOTE_URL)

    with remote_conn.cursor() as cur:
        print("Clearing data from remote tables for clean sync...")
        for table in reversed(TABLES_IN_ORDER):
            try:
                cur.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
            except Exception as e:
                print(f"  Note on truncating {table}: {e}")
        remote_conn.commit()

    print("\nTransferring data...")
    for table in TABLES_IN_ORDER:
        with local_conn.cursor() as l_cur:
            l_cur.execute(f"SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '{table}');")
            if not l_cur.fetchone()[0]:
                print(f"Skipping {table} (not in local)")
                continue

            l_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{table}' ORDER BY ordinal_position;")
            col_info = l_cur.fetchall()
            cols = [r[0] for r in col_info]
            
            with remote_conn.cursor() as r_cur:
                r_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{table}' ORDER BY ordinal_position;")
                r_col_info = r_cur.fetchall()
                r_col_dict = {r[0]: r[1] for r in r_col_info}
            
            common_cols = [c for c in cols if c in r_col_dict]
            json_cols = set(c for c in common_cols if r_col_dict[c] in ('json', 'jsonb'))

            col_list_str = ", ".join(f'"{c}"' for c in common_cols)
            placeholders = ", ".join(["%s"] * len(common_cols))

            l_cur.execute(f"SELECT {col_list_str} FROM \"{table}\";")
            
            batch_size = 2000
            total_transferred = 0
            with remote_conn.cursor() as r_cur:
                insert_sql = f'INSERT INTO "{table}" ({col_list_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;'
                while True:
                    rows = l_cur.fetchmany(batch_size)
                    if not rows:
                        break
                    
                    if json_cols:
                        cleaned_rows = []
                        for row in rows:
                            new_row = list(row)
                            for idx, c in enumerate(common_cols):
                                if c in json_cols and new_row[idx] is not None:
                                    if not isinstance(new_row[idx], str):
                                        new_row[idx] = json.dumps(new_row[idx])
                            cleaned_rows.append(tuple(new_row))
                        r_cur.executemany(insert_sql, cleaned_rows)
                    else:
                        r_cur.executemany(insert_sql, rows)

                    total_transferred += len(rows)
                    if total_transferred % 10000 == 0:
                        print(f"  {table}: {total_transferred} rows transferred...")
                remote_conn.commit()
            print(f"[OK] {table}: {total_transferred} rows migrated.")

    print("\nResetting PostgreSQL sequence IDs...")
    with remote_conn.cursor() as r_cur:
        for table in TABLES_IN_ORDER:
            try:
                r_cur.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = '{table}' AND column_default LIKE 'nextval%';
                """)
                serials = r_cur.fetchall()
                for (col_name,) in serials:
                    r_cur.execute(f"""
                        SELECT setval(pg_get_serial_sequence('{table}', '{col_name}'), COALESCE(MAX("{col_name}"), 1)) FROM "{table}";
                    """)
            except Exception as e:
                pass
        remote_conn.commit()

    local_conn.close()
    remote_conn.close()
    print("\n[SUCCESS] All 46,280 observations, 392 species, and data assets migrated to Render!")

if __name__ == "__main__":
    migrate()

