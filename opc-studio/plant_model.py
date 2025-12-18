"""
Plant Model - Semantic representation of manufacturing plant
"""
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Station:
    """Manufacturing station"""
    station_id: str
    station_name: str
    station_type: str
    sequence: int
    
    def to_dict(self) -> dict:
        return {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "station_type": self.station_type,
            "sequence": self.sequence
        }


@dataclass
class ProductionLine:
    """Production line with stations"""
    line_id: str
    line_name: str
    stations: List[Station] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "line_id": self.line_id,
            "line_name": self.line_name,
            "stations": [s.to_dict() for s in self.stations]
        }


class PlantModel:
    """Plant model manager"""
    
    def __init__(self):
        self.production_lines: List[ProductionLine] = []
        self._lines_by_id: dict = {}
    
    async def load_model(self):
        """Load plant model from file or create default"""
        model_path = Path("/app/models/plant_model.json")
        
        if model_path.exists():
            logger.info(f"Loading plant model from {model_path}")
            with open(model_path, 'r') as f:
                data = json.load(f)
                self._parse_model(data)
        else:
            logger.info("Creating default plant model")
            self._create_default_model()
    
    def _parse_model(self, data: dict):
        """Parse plant model from JSON data"""
        for line_data in data.get("production_lines", []):
            line = ProductionLine(
                line_id=line_data["line_id"],
                line_name=line_data["line_name"]
            )
            
            for station_data in line_data.get("stations", []):
                station = Station(
                    station_id=station_data["station_id"],
                    station_name=station_data["station_name"],
                    station_type=station_data.get("station_type", "processing"),
                    sequence=station_data.get("sequence", 0)
                )
                line.stations.append(station)
            
            self.production_lines.append(line)
            self._lines_by_id[line.line_id] = line
    
    def _create_default_model(self):
        """Create default plant model with 3 production lines"""
        lines_config = [
            {
                "line_id": "LINE_A",
                "line_name": "Assembly Line A",
                "stations": [
                    {"id": "ST_A1", "name": "Loading Station", "type": "loading"},
                    {"id": "ST_A2", "name": "Assembly Robot 1", "type": "assembly"},
                    {"id": "ST_A3", "name": "Assembly Robot 2", "type": "assembly"},
                    {"id": "ST_A4", "name": "Quality Check", "type": "inspection"},
                    {"id": "ST_A5", "name": "Packaging", "type": "packaging"}
                ]
            },
            {
                "line_id": "LINE_B",
                "line_name": "Assembly Line B",
                "stations": [
                    {"id": "ST_B1", "name": "Loading Station", "type": "loading"},
                    {"id": "ST_B2", "name": "Welding Robot", "type": "welding"},
                    {"id": "ST_B3", "name": "Assembly Station", "type": "assembly"},
                    {"id": "ST_B4", "name": "Testing", "type": "testing"},
                    {"id": "ST_B5", "name": "Packaging", "type": "packaging"}
                ]
            },
            {
                "line_id": "LINE_C",
                "line_name": "Packaging Line C",
                "stations": [
                    {"id": "ST_C1", "name": "Receiving", "type": "receiving"},
                    {"id": "ST_C2", "name": "Labeling", "type": "labeling"},
                    {"id": "ST_C3", "name": "Sealing", "type": "sealing"},
                    {"id": "ST_C4", "name": "Palletizing", "type": "palletizing"}
                ]
            }
        ]
        
        for line_cfg in lines_config:
            line = ProductionLine(
                line_id=line_cfg["line_id"],
                line_name=line_cfg["line_name"]
            )
            
            for idx, station_cfg in enumerate(line_cfg["stations"], start=1):
                station = Station(
                    station_id=station_cfg["id"],
                    station_name=station_cfg["name"],
                    station_type=station_cfg["type"],
                    sequence=idx
                )
                line.stations.append(station)
            
            self.production_lines.append(line)
            self._lines_by_id[line.line_id] = line
    
    def get_line(self, line_id: str) -> Optional[ProductionLine]:
        """Get production line by ID"""
        return self._lines_by_id.get(line_id)
    
    def to_dict(self) -> dict:
        """Export plant model to dict"""
        return {
            "production_lines": [line.to_dict() for line in self.production_lines],
            "total_lines": len(self.production_lines),
            "total_stations": sum(len(line.stations) for line in self.production_lines)
        }
