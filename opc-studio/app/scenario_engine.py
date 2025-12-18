"""
Scenario Template Engine
Loads taxonomy and templates, applies severity levels and cascading impacts
"""
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional

class ScenarioEngine:
    """Manages scenario templates, taxonomy, and cascading logic"""
    
    def __init__(self, models_dir: str = "/app/models"):
        self.models_dir = Path(models_dir)
        self.taxonomy = self._load_json("scenario_taxonomy.json")
        self.templates = self._load_json("scenario_templates.json")
        
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON file from models directory"""
        path = self.models_dir / filename
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}
    
    def get_taxonomy(self) -> Dict[str, Any]:
        """Get full taxonomy structure"""
        return self.taxonomy
    
    def get_severity_levels(self) -> Dict[str, Any]:
        """Get severity level definitions"""
        return self.taxonomy.get("severity_levels", {})
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get all scenario templates"""
        return self.templates.get("templates", [])
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get specific template by ID"""
        for template in self.get_templates():
            if template.get("id") == template_id:
                return template
        return None
    
    def get_templates_for_station(self, station_type: str) -> List[Dict[str, Any]]:
        """Get templates applicable to specific station type"""
        results = []
        for template in self.get_templates():
            applicable = template.get("applicable_station_types", [])
            if station_type in applicable:
                results.append(template)
        return results
    
    def apply_template(self, template_id: str, line_state: Dict, station_state: Dict, 
                      severity_override: Optional[str] = None) -> Dict[str, Any]:
        """Apply scenario template with cascading logic
        
        Args:
            template_id: ID of template to apply
            line_state: Current line state dict
            station_state: Current station state dict  
            severity_override: Optional severity override (minor/moderate/major/critical)
            
        Returns:
            Dict with applied impacts and cascading effects
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return {"error": f"Template '{template_id}' not found"}
        
        severity = severity_override or template.get("severity", "moderate")
        severity_def = self.get_severity_levels().get(severity, {})
        
        # Calculate base impacts from template
        impact = template.get("impact", {})
        
        # Apply randomization within severity range
        severity_impact = severity_def.get("impact", {})
        randomized_impact = {}
        for metric in ["availability", "performance", "quality"]:
            base = impact.get(metric, 0)
            severity_range = severity_impact.get(metric, [0, 0])
            # Add some randomness within severity bounds
            random_factor = random.uniform(severity_range[0], severity_range[1])
            randomized_impact[metric] = max(-1.0, min(0.0, base + random_factor * 0.3))
        
        # Determine cascading effects
        cascading_effects = []
        if template.get("cascading", False):
            station_critical = station_state.get("critical", False)
            
            # Check cascading rules from taxonomy
            rules = self.taxonomy.get("cascading_rules", {})
            
            # Critical station down rule
            if station_critical and randomized_impact["availability"] < -0.3:
                rule = rules.get("critical_station_down", {})
                cascading_effects.append({
                    "rule": "critical_station_down",
                    "description": rule.get("description", ""),
                    "effects": rule.get("effects", [])
                })
            
            # Material shortage rule
            if "material_shortage" in template.get("category", ""):
                rule = rules.get("material_shortage", {})
                cascading_effects.append({
                    "rule": "material_shortage",
                    "description": rule.get("description", ""),
                    "effects": rule.get("effects", []),
                    "delay_min": template.get("cascading_delay_min", 0)
                })
            
            # Quality issue rule
            if "quality_issue" in template.get("category", ""):
                rule = rules.get("quality_issue", {})
                cascading_effects.append({
                    "rule": "quality_issue",
                    "description": rule.get("description", ""),
                    "effects": rule.get("effects", [])
                })
        
        return {
            "template": template,
            "severity": severity,
            "duration_min": template.get("duration_min", 15),
            "impact": randomized_impact,
            "alarms": template.get("alarms", []),
            "cascading_effects": cascading_effects,
            "description": template.get("description", "")
        }
    
    def get_event_categories(self) -> List[Dict[str, str]]:
        """Get flattened list of event categories for UI dropdowns"""
        categories = []
        taxonomy = self.taxonomy.get("taxonomy", {})
        
        for main_cat_key, main_cat in taxonomy.items():
            for sub_cat_key, sub_cat in main_cat.get("categories", {}).items():
                for event in sub_cat.get("events", []):
                    categories.append({
                        "id": f"{main_cat_key}.{sub_cat_key}.{event}",
                        "name": event.replace("_", " ").title(),
                        "main_category": main_cat.get("name", ""),
                        "sub_category": sub_cat.get("name", "")
                    })
        
        return categories


# Global instance
_engine = None

def get_scenario_engine(models_dir: str = "/app/models") -> ScenarioEngine:
    """Get or create global ScenarioEngine instance"""
    global _engine
    if _engine is None:
        _engine = ScenarioEngine(models_dir)
    return _engine
