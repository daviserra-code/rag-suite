"""
Import OEE CSV data into PostgreSQL
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text

def get_db_engine():
    """Create SQLAlchemy engine for PostgreSQL"""
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "mes_db")
    DB_USER = os.getenv("POSTGRES_USER", "mes_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "mes_pass")
    
    connection_string = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

def import_oee_data(dataset_name="shopfloor_oee_dataset", use_wide=True, use_year=False):
    """Import OEE CSV files into PostgreSQL"""
    engine = get_db_engine()
    base_path = f"./data/documents/{dataset_name}"
    
    # Determine suffix based on dataset type
    if use_year:
        suffix = "_year"
    elif use_wide:
        suffix = "_wide"
    else:
        suffix = ""
    
    print("🔄 Importing OEE data into PostgreSQL...")
    print(f"📁 Dataset: {dataset_name} (suffix={suffix})")
    
    # 1. Import oee_line_shift
    print("\n📊 Importing oee_line_shift.csv...")
    df_line = pd.read_csv(f"{base_path}/oee_line_shift{suffix}.csv")
    df_line['date'] = pd.to_datetime(df_line['date'])
    
    with engine.begin() as conn:
        # Drop and recreate table
        conn.execute(text("DROP TABLE IF EXISTS oee_line_shift CASCADE"))
        conn.execute(text("""
            CREATE TABLE oee_line_shift (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                shift VARCHAR(10) NOT NULL,
                line_id VARCHAR(50) NOT NULL,
                line_name VARCHAR(100),
                planned_time_min FLOAT,
                unplanned_downtime_min FLOAT,
                operating_time_min FLOAT,
                ideal_cycle_time_sec FLOAT,
                theoretical_output_units INTEGER,
                total_units_produced INTEGER,
                good_units INTEGER,
                scrap_units INTEGER,
                availability FLOAT,
                performance FLOAT,
                quality FLOAT,
                oee FLOAT,
                main_loss_category VARCHAR(100),
                UNIQUE(date, shift, line_id)
            )
        """))
    
    # Import line shifts in chunks to avoid PostgreSQL text limit
    chunk_size = 100  # Smaller chunks for year dataset
    total_chunks = (len(df_line) + chunk_size - 1) // chunk_size
    for i in range(0, len(df_line), chunk_size):
        chunk = df_line.iloc[i:i+chunk_size]
        chunk.to_sql('oee_line_shift', engine, if_exists='append', index=False, method='multi')
        print(f"  Imported chunk {i//chunk_size + 1}/{total_chunks} ({len(chunk)} rows)")
    print(f"✅ Imported {len(df_line)} rows into oee_line_shift")
    
    # 2. Import oee_station_shift
    print("\n📊 Importing oee_station_shift.csv...")
    df_station = pd.read_csv(f"{base_path}/oee_station_shift{suffix}.csv")
    df_station['date'] = pd.to_datetime(df_station['date'])
    
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS oee_station_shift CASCADE"))
        conn.execute(text("""
            CREATE TABLE oee_station_shift (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                shift VARCHAR(10) NOT NULL,
                line_id VARCHAR(50) NOT NULL,
                line_name VARCHAR(100),
                station_id VARCHAR(50) NOT NULL,
                planned_time_min FLOAT,
                unplanned_downtime_min FLOAT,
                operating_time_min FLOAT,
                total_units_produced INTEGER,
                good_units INTEGER,
                scrap_units INTEGER,
                availability FLOAT,
                performance FLOAT,
                quality FLOAT,
                oee FLOAT,
                UNIQUE(date, shift, line_id, station_id)
            )
        """))
    
    # Import in chunks to avoid PostgreSQL text limit
    chunk_size = 100  # Smaller chunks for year dataset
    total_chunks = (len(df_station) + chunk_size - 1) // chunk_size
    for i in range(0, len(df_station), chunk_size):
        chunk = df_station.iloc[i:i+chunk_size]
        chunk.to_sql('oee_station_shift', engine, if_exists='append', index=False, method='multi')
        print(f"  Imported chunk {i//chunk_size + 1}/{total_chunks} ({len(chunk)} rows)")
    print(f"✅ Imported {len(df_station)} rows into oee_station_shift")
    
    # 3. Import oee_downtime_events
    print("\n📊 Importing oee_downtime_events.csv...")
    df_downtime = pd.read_csv(f"{base_path}/oee_downtime_events{suffix}.csv")
    df_downtime['date'] = pd.to_datetime(df_downtime['date'])
    df_downtime['start_timestamp'] = pd.to_datetime(df_downtime['start_timestamp'])
    
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS oee_downtime_events CASCADE"))
        conn.execute(text("""
            CREATE TABLE oee_downtime_events (
                event_id INTEGER PRIMARY KEY,
                line_id VARCHAR(50) NOT NULL,
                line_name VARCHAR(100),
                date DATE NOT NULL,
                shift VARCHAR(10) NOT NULL,
                start_timestamp TIMESTAMP NOT NULL,
                duration_min FLOAT,
                loss_category VARCHAR(100),
                description TEXT
            )
        """))
    
    # Import in chunks to avoid PostgreSQL text limit
    chunk_size = 100  # Smaller chunks for year dataset
    total_chunks = (len(df_downtime) + chunk_size - 1) // chunk_size
    for i in range(0, len(df_downtime), chunk_size):
        chunk = df_downtime.iloc[i:i+chunk_size]
        chunk.to_sql('oee_downtime_events', engine, if_exists='append', index=False, method='multi')
        print(f"  Imported chunk {i//chunk_size + 1}/{total_chunks} ({len(chunk)} rows)")
    print(f"✅ Imported {len(df_downtime)} rows into oee_downtime_events")
    
    # 4. Create useful indexes
    print("\n🔍 Creating indexes...")
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX idx_line_shift_date ON oee_line_shift(date, line_id, shift)"))
        conn.execute(text("CREATE INDEX idx_station_shift_date ON oee_station_shift(date, line_id, station_id)"))
        conn.execute(text("CREATE INDEX idx_downtime_date ON oee_downtime_events(date, line_id)"))
    
    print("\n✅ OEE data import completed successfully!")
    
    # Show summary
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT 
                line_id,
                COUNT(*) as records,
                MIN(date) as start_date,
                MAX(date) as end_date,
                ROUND(AVG(oee)::numeric, 3) as avg_oee
            FROM oee_line_shift
            GROUP BY line_id
            ORDER BY line_id
        """))
        
        print("\n📈 Summary by Line:")
        for row in result:
            print(f"  {row.line_id}: {row.records} records, {row.start_date} to {row.end_date}, Avg OEE: {row.avg_oee}")

if __name__ == "__main__":
    import_oee_data(dataset_name="shopfloor_oee_dataset_year", use_wide=False, use_year=True)

