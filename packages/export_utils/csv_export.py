"""CSV Export Utilities"""

import csv
import io
from typing import List, Dict
from datetime import datetime


def export_to_csv(data: List[Dict], filename: str = None, columns: List[str] = None) -> str:
    """
    Export data to CSV format
    
    Args:
        data: List of dictionaries with data
        filename: Optional filename (auto-generated if not provided)
        columns: Optional list of column names (uses all keys if not provided)
    
    Returns:
        CSV content as string
    """
    if not data:
        return ""
    
    # Auto-generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.csv"
    
    # Determine columns
    if not columns:
        columns = list(data[0].keys())
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    
    # Write header
    writer.writeheader()
    
    # Write data rows
    for row in data:
        writer.writerow(row)
    
    return output.getvalue()


def create_csv_download(data: List[Dict], filename: str, columns: List[str] = None) -> bytes:
    """
    Create CSV file content ready for download
    
    Args:
        data: List of dictionaries with data
        filename: Filename for download
        columns: Optional list of column names
    
    Returns:
        CSV content as bytes
    """
    csv_content = export_to_csv(data, filename, columns)
    return csv_content.encode('utf-8')
