"""
Last sync timestamp tracking for incremental updates
"""
import json
import os
from datetime import datetime
from typing import Optional

class SyncTracker:
    """Track last sync timestamps for incremental updates"""
    
    def __init__(self, tracker_file: str = 'last_sync.json'):
        self.tracker_file = tracker_file
        self.sync_data = self._load_tracker()
    
    def _load_tracker(self) -> dict:
        """Load sync tracking data from file"""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_tracker(self):
        """Save sync tracking data to file"""
        try:
            with open(self.tracker_file, 'w') as f:
                json.dump(self.sync_data, f, indent=2, default=str)
        except IOError as e:
            print(f"Warning: Could not save sync tracker: {e}")
    
    def get_last_sync(self, table_name: str) -> Optional[str]:
        """Get last sync timestamp for a table"""
        return self.sync_data.get(table_name, {}).get('last_sync')
    
    def set_last_sync(self, table_name: str, timestamp: str):
        """Set last sync timestamp for a table"""
        if table_name not in self.sync_data:
            self.sync_data[table_name] = {}
        
        self.sync_data[table_name]['last_sync'] = timestamp
        self.sync_data[table_name]['updated_at'] = datetime.now().isoformat()
        self._save_tracker()
    
    def get_incremental_condition(self, table_name: str, timestamp_column: str, 
                                 base_condition: Optional[str] = None) -> str:
        """Build incremental sync condition"""
        last_sync = self.get_last_sync(table_name)
        
        conditions = []
        
        # Add base condition if exists
        if base_condition:
            conditions.append(f"({base_condition})")
        
        # Add incremental condition
        if last_sync:
            conditions.append(f"{timestamp_column} > '{last_sync}'")
        
        return " AND ".join(conditions) if conditions else ""
    
    def clear_last_sync(self, table_name: str):
        """Clear last sync timestamp (force full sync)"""
        if table_name in self.sync_data:
            del self.sync_data[table_name]
            self._save_tracker()