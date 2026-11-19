import sqlite3

def run_migrations():
    conn = sqlite3.connect('wildlife_dev.db')
    cursor = conn.cursor()

    # 1. Check observations table
    cursor.execute('PRAGMA table_info(observations);')
    obs_cols = [c[1] for c in cursor.fetchall()]
    if 'external_id' not in obs_cols:
        cursor.execute('ALTER TABLE observations ADD COLUMN external_id VARCHAR(200);')
        print('Added external_id to observations')

    # 2. Check ml_anomalies table
    cursor.execute('PRAGMA table_info(ml_anomalies);')
    anom_cols = [c[1] for c in cursor.fetchall()]
    if 'status' not in anom_cols:
        cursor.execute("ALTER TABLE ml_anomalies ADD COLUMN status VARCHAR(50) DEFAULT 'OPEN';")
        print('Added status to ml_anomalies')
    if 'acknowledged' not in anom_cols:
        cursor.execute('ALTER TABLE ml_anomalies ADD COLUMN acknowledged BOOLEAN DEFAULT 0;')
        print('Added acknowledged to ml_anomalies')
    if 'acknowledged_by_id' not in anom_cols:
        cursor.execute('ALTER TABLE ml_anomalies ADD COLUMN acknowledged_by_id INTEGER;')
        print('Added acknowledged_by_id to ml_anomalies')
    if 'acknowledged_at' not in anom_cols:
        cursor.execute('ALTER TABLE ml_anomalies ADD COLUMN acknowledged_at DATETIME;')
        print('Added acknowledged_at to ml_anomalies')
    if 'investigation_notes' not in anom_cols:
        cursor.execute('ALTER TABLE ml_anomalies ADD COLUMN investigation_notes TEXT;')
        print('Added investigation_notes to ml_anomalies')

    conn.commit()
    conn.close()
    print('SQLite migration check complete successfully')

if __name__ == '__main__':
    run_migrations()
