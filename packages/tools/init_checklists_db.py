"""Initialize checklist database tables"""
import os
import psycopg
from datetime import datetime

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "ragdb")

def init_checklist_tables():
    """Create checklist tables"""
    conn_string = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
    
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            # Checklists table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checklists (
                    id SERIAL PRIMARY KEY,
                    line_id VARCHAR(50) NOT NULL,
                    section VARCHAR(100),
                    checklist_type VARCHAR(100),
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Checklist items table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checklist_items (
                    id SERIAL PRIMARY KEY,
                    checklist_id INTEGER REFERENCES checklists(id) ON DELETE CASCADE,
                    sequence_number INTEGER NOT NULL,
                    item_text TEXT NOT NULL,
                    is_critical BOOLEAN DEFAULT FALSE,
                    reference_document VARCHAR(255)
                )
            """)
            
            # Checklist executions table (tracking)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checklist_executions (
                    id SERIAL PRIMARY KEY,
                    checklist_id INTEGER REFERENCES checklists(id),
                    line_id VARCHAR(50) NOT NULL,
                    executed_by VARCHAR(100),
                    execution_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completion_status VARCHAR(50),
                    notes TEXT
                )
            """)
            
            # Checklist execution items (individual item completion)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checklist_execution_items (
                    id SERIAL PRIMARY KEY,
                    execution_id INTEGER REFERENCES checklist_executions(id) ON DELETE CASCADE,
                    item_id INTEGER REFERENCES checklist_items(id),
                    is_completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    notes TEXT
                )
            """)
            
            # Create indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_checklists_line 
                ON checklists(line_id, is_active)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_checklist_items_checklist 
                ON checklist_items(checklist_id, sequence_number)
            """)
            
            conn.commit()
            
            # Insert sample checklists
            insert_sample_checklists(cur)
            conn.commit()
            
            print("✅ Checklist tables created successfully")

def insert_sample_checklists(cur):
    """Insert sample checklists for each line"""
    
    lines = ['M10', 'B02', 'C03', 'D01', 'SMT1', 'WC01']
    
    for line in lines:
        # Startup checklist
        cur.execute("""
            INSERT INTO checklists (line_id, section, checklist_type, title, description, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (line, line, 'Startup', f'{line} - Startup Procedure', 
              f'Standard startup checklist for production line {line}', 'System'))
        
        checklist_id = cur.fetchone()[0]
        
        # Add startup items
        startup_items = [
            ('Verify emergency stop is released', True),
            ('Check all safety guards are in place', True),
            ('Activate main disconnect switch', True),
            ('Verify compressed air supply pressure (6-8 bar)', False),
            ('Check hydraulic fluid levels', False),
            ('Verify all sensors are operational', True),
            ('Test emergency stop functionality', True),
            ('Press green start button', False),
            ('Monitor initial operation for abnormal sounds', False),
            ('Verify product quality on first piece', True)
        ]
        
        for idx, (item_text, is_critical) in enumerate(startup_items, 1):
            cur.execute("""
                INSERT INTO checklist_items (checklist_id, sequence_number, item_text, is_critical)
                VALUES (%s, %s, %s, %s)
            """, (checklist_id, idx, item_text, is_critical))
        
        # Shutdown checklist
        cur.execute("""
            INSERT INTO checklists (line_id, section, checklist_type, title, description, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (line, line, 'Shutdown', f'{line} - Shutdown Procedure',
              f'Standard shutdown checklist for production line {line}', 'System'))
        
        checklist_id = cur.fetchone()[0]
        
        # Add shutdown items
        shutdown_items = [
            ('Complete current production run', False),
            ('Press red stop button', False),
            ('Wait for all moving parts to stop', True),
            ('Disconnect main power supply', True),
            ('Release compressed air pressure', False),
            ('Clean work area and equipment', False),
            ('Remove all product and materials', False),
            ('Inspect equipment for damage or wear', False),
            ('Complete shift handover log', False),
            ('Engage emergency stop for lockout', True)
        ]
        
        for idx, (item_text, is_critical) in enumerate(shutdown_items, 1):
            cur.execute("""
                INSERT INTO checklist_items (checklist_id, sequence_number, item_text, is_critical)
                VALUES (%s, %s, %s, %s)
            """, (checklist_id, idx, item_text, is_critical))
    
    print(f"✅ Sample checklists created for {len(lines)} lines")

if __name__ == "__main__":
    init_checklist_tables()
