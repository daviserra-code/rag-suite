"""
Historian Bridge - Syncs OPC UA data to PostgreSQL
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class HistorianBridge:
    """Bridges OPC UA server data to PostgreSQL database"""
    
    def __init__(self, opc_server):
        self.opc_server = opc_server
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
        self._last_sync: Optional[datetime] = None
        self._sync_count = 0
        
        # Database connection
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")
        self.engine = create_engine(db_url, poolclass=NullPool)
    
    async def start(self):
        """Start the historian bridge"""
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Historian bridge started")
    
    async def stop(self):
        """Stop the historian bridge"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Historian bridge stopped")
    
    def is_running(self) -> bool:
        """Check if bridge is running"""
        return self._running
    
    def get_last_sync_time(self) -> Optional[str]:
        """Get last sync timestamp"""
        return self._last_sync.isoformat() if self._last_sync else None
    
    def get_stats(self) -> dict:
        """Get historian statistics"""
        return {
            "running": self._running,
            "last_sync": self.get_last_sync_time(),
            "sync_count": self._sync_count,
            "sync_interval_seconds": 30
        }
    
    async def _sync_loop(self):
        """Periodic sync loop"""
        try:
            while self._running:
                await self.sync_to_database()
                await asyncio.sleep(30)  # Sync every 30 seconds
        except asyncio.CancelledError:
            logger.info("Sync loop cancelled")
    
    async def sync_to_database(self):
        """Sync OPC UA data to database"""
        try:
            # Read current values from OPC UA server
            plant_data = await self._read_plant_data()
            
            # Write to database
            await asyncio.to_thread(self._write_to_db, plant_data)
            
            self._last_sync = datetime.now()
            self._sync_count += 1
            
            logger.info(f"Sync #{self._sync_count} completed at {self._last_sync}")
            
        except Exception as e:
            logger.error(f"Error during sync: {e}", exc_info=True)
    
    async def _read_plant_data(self) -> dict:
        """Read all relevant data from OPC UA server"""
        data = {
            "timestamp": datetime.now(),
            "lines": []
        }
        
        for line in self.opc_server.plant_model.production_lines:
            line_path = f"Plant.{line.line_id}"
            
            try:
                # Read line metrics
                oee = await self.opc_server.read_node(f"{line_path}.OEE")
                availability = await self.opc_server.read_node(f"{line_path}.Availability")
                performance = await self.opc_server.read_node(f"{line_path}.Performance")
                quality = await self.opc_server.read_node(f"{line_path}.Quality")
                
                line_data = {
                    "line_id": line.line_id,
                    "line_name": line.line_name,
                    "oee": float(oee),
                    "availability": float(availability),
                    "performance": float(performance),
                    "quality": float(quality),
                    "stations": []
                }
                
                # Read station data
                for station in line.stations:
                    station_path = f"{line_path}.{station.station_id}"
                    
                    try:
                        status = await self.opc_server.read_node(f"{station_path}.Status")
                        temperature = await self.opc_server.read_node(f"{station_path}.Temperature")
                        cycle_time = await self.opc_server.read_node(f"{station_path}.CycleTime")
                        
                        station_data = {
                            "station_id": station.station_id,
                            "status": str(status),
                            "temperature": float(temperature),
                            "cycle_time": float(cycle_time)
                        }
                        line_data["stations"].append(station_data)
                    except Exception as e:
                        logger.error(f"Error reading station {station.station_id}: {e}")
                
                data["lines"].append(line_data)
                
            except Exception as e:
                logger.error(f"Error reading line {line.line_id}: {e}")
        
        return data
    
    def _write_to_db(self, plant_data: dict):
        """Write plant data to PostgreSQL"""
        try:
            with self.engine.begin() as conn:
                timestamp = plant_data["timestamp"]
                
                # Insert into opc_realtime_data table (create if not exists)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS opc_realtime_data (
                        id SERIAL PRIMARY KEY,
                        line_id VARCHAR(50),
                        line_name VARCHAR(200),
                        station_id VARCHAR(50),
                        oee NUMERIC(5,4),
                        availability NUMERIC(5,4),
                        performance NUMERIC(5,4),
                        quality NUMERIC(5,4),
                        status VARCHAR(50),
                        temperature NUMERIC(6,2),
                        cycle_time NUMERIC(8,2),
                        timestamp TIMESTAMP DEFAULT NOW()
                    )
                """))
                
                # Insert line-level data
                for line in plant_data["lines"]:
                    conn.execute(text("""
                        INSERT INTO opc_realtime_data 
                        (line_id, line_name, oee, availability, performance, quality, timestamp)
                        VALUES (:line_id, :line_name, :oee, :availability, :performance, :quality, :timestamp)
                    """), {
                        "line_id": line["line_id"],
                        "line_name": line["line_name"],
                        "oee": line["oee"],
                        "availability": line["availability"],
                        "performance": line["performance"],
                        "quality": line["quality"],
                        "timestamp": timestamp
                    })
                    
                    # Insert station-level data
                    for station in line["stations"]:
                        conn.execute(text("""
                            INSERT INTO opc_realtime_data 
                            (line_id, line_name, station_id, status, temperature, cycle_time, timestamp)
                            VALUES (:line_id, :line_name, :station_id, :status, :temperature, :cycle_time, :timestamp)
                        """), {
                            "line_id": line["line_id"],
                            "line_name": line["line_name"],
                            "station_id": station["station_id"],
                            "status": station["status"],
                            "temperature": station["temperature"],
                            "cycle_time": station["cycle_time"],
                            "timestamp": timestamp
                        })
                
                logger.debug(f"Wrote {len(plant_data['lines'])} lines to database")
                
        except Exception as e:
            logger.error(f"Error writing to database: {e}", exc_info=True)
            raise
