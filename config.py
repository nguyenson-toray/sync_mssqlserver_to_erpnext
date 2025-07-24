"""
Database Configuration for MSSQL to MariaDB Sync
"""
import os
import json
import shutil
import subprocess
from typing import Dict, Any, Optional, List

class DatabaseConfig:
    """Database configuration class with environment variable support"""
    
    def __init__(self):
        self.mssql_config = {
            'server': os.getenv('MSSQL_SERVER', '10.0.1.4'),
            'database': os.getenv('MSSQL_DATABASE', 'Production'),
            'username': os.getenv('MSSQL_USERNAME', 'production'),
            'password': os.getenv('MSSQL_PASSWORD', 'Toray@123'),
            'port': int(os.getenv('MSSQL_PORT', '1433'))
        }
        
        # Auto-detect ERPNext site database
        database_name = self._get_site_database_name()
        
        self.mariadb_config = {
            'host': os.getenv('MARIADB_HOST', 'localhost'),
            'database': os.getenv('MARIADB_DATABASE', database_name),
            'user': os.getenv('MARIADB_USER', 'root'),
            'password': os.getenv('MARIADB_PASSWORD', 'T0ray25#'),
            'port': int(os.getenv('MARIADB_PORT', '3306'))
        }
        
        self.sync_config = {
            'batch_size': int(os.getenv('SYNC_BATCH_SIZE', '1000')),
            'max_retries': int(os.getenv('SYNC_MAX_RETRIES', '3'))
        }
        
        # Table sync configuration
        self.table_sync_config = self._load_table_config()
    
    @property
    def mssql_command(self) -> list:
        """Generate MSSQL command string for subprocess calls"""
        # Try different SQL Server client tools in order of preference
        
        # Option 1: sqlcmd (Microsoft SQL Server command line)
        if shutil.which('sqlcmd'):
            return [
                'sqlcmd',
                '-S', self.mssql_config['server'],
                '-U', self.mssql_config['username'],
                '-P', self.mssql_config['password'],
                '-d', self.mssql_config['database'],
                '-h', '-1',  # No headers
                '-W'         # Remove trailing spaces
            ]
        
        # Option 2: tsql (FreeTDS)
        elif shutil.which('tsql'):
            return [
                'tsql', 
                '-S', self.mssql_config['server'],
                '-U', self.mssql_config['username'],
                '-P', self.mssql_config['password'],
                '-D', self.mssql_config['database']
            ]
        
        # No SQL Server client found
        else:
            raise RuntimeError(
                "No SQL Server client found. Please install one of:\n"
                "1. sqlcmd (Microsoft SQL Server tools)\n"
                "2. tsql (FreeTDS): sudo apt-get install freetds-bin"
            )
    
    @property 
    def mssql_client_type(self) -> str:
        """Get the type of MSSQL client being used"""
        if shutil.which('sqlcmd'):
            return 'sqlcmd'
        elif shutil.which('tsql'):
            return 'tsql'
        else:
            return 'none'
    
    def get_mssql_config(self) -> Dict[str, Any]:
        return self.mssql_config.copy()
    
    def get_mariadb_config(self) -> Dict[str, Any]:
        return self.mariadb_config.copy()
    
    def get_sync_config(self) -> Dict[str, Any]:
        return self.sync_config.copy()
    
    def _get_site_database_name(self) -> str:
        """Auto-detect database name from ERPNext site configuration"""
        # Try environment variable first
        env_db = os.getenv('MARIADB_DATABASE')
        if env_db:
            return env_db
        
        # Try site config detection
        db_name = self._detect_from_site_configs() or self._detect_from_bench_command()
        
        if db_name:
            return db_name
        
        # Fallback
        site_name = os.getenv('ERPNEXT_SITE', 'erp-sonnt.tiqn.local')
        return site_name.replace('.', '_').replace('-', '_')
    
    def _detect_from_site_configs(self) -> Optional[str]:
        """Try to detect database name from site configuration files"""
        current_dir = os.getcwd()
        search_paths = [
            current_dir,
            os.path.dirname(current_dir),
            os.path.join(os.path.dirname(current_dir), '..'),
        ]
        
        # Look for sites directory and site_config.json
        for base_path in search_paths:
            sites_dir = os.path.join(base_path, 'sites')
            if not os.path.exists(sites_dir):
                continue
                
            for item in os.listdir(sites_dir):
                site_config_path = os.path.join(sites_dir, item, 'site_config.json')
                if os.path.exists(site_config_path):
                    try:
                        with open(site_config_path, 'r') as f:
                            config = json.load(f)
                            if config.get('db_name'):
                                return config['db_name']
                    except (json.JSONDecodeError, IOError):
                        continue
        
        # Check common config files
        common_paths = [
            '/home/frappe/frappe-bench/config/common_site_config.json',
            '../config/common_site_config.json',
            os.path.join(os.path.dirname(current_dir), 'config', 'common_site_config.json')
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        config = json.load(f)
                        if 'default_site' in config:
                            return config['default_site'].replace('.', '_').replace('-', '_')
                except (json.JSONDecodeError, IOError):
                    continue
        
        return None
    
    def _detect_from_bench_command(self) -> Optional[str]:
        """Try to detect using bench command"""
        try:
            result = subprocess.run(['bench', 'list-sites'], 
                                 capture_output=True, text=True, 
                                 cwd=os.path.dirname(os.getcwd()))
            if result.returncode == 0:
                sites = result.stdout.strip().split('\n')
                if sites and sites[0]:
                    return sites[0].replace('.', '_').replace('-', '_')
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None
    
    def _load_table_config(self) -> Dict[str, Any]:
        """Load table synchronization configuration"""
        return {
            # Example: Sync all columns from T50_InspectionData
            'T50_InspectionData': {
                'sync': True,
                'columns': None,  # None means all columns
                'condition': None, #"X02 > '2025-03-31'",  # X02 is the datetime column
                'sync_mode': 'incremental',  # 'full' or 'incremental'
                'timestamp_column': 'X02',  # Column for incremental sync tracking
                'primary_key': 'ID',  # Primary key for upsert operations
                'column_mapping': {  # Map MSSQL columns to MariaDB columns
                    '2nd': 'inspection_type',  # Rename problematic column names
                    'X02': 'inspection_date',  # More descriptive names
                    'XC': 'comments'
                    # Add more mappings as needed
                }
            },
             'T50_InspectionData': {
                'sync': True,
                'columns': None,  # None means all columns
                'condition': None, #"X02 > '2025-03-31'",  # X02 is the datetime column
                'sync_mode': 'incremental',  # 'full' or 'incremental'
                'timestamp_column': 'X02',  # Column for incremental sync tracking
                'primary_key': 'ID',  # Primary key for upsert operations
                'column_mapping': {  # Map MSSQL columns to MariaDB columns
                    '2nd': 'inspection_type',  # Rename problematic column names
                    'X01': 'line',
                    'X02': 'date',  # More descriptive names
                    'X03': 'stye_no',
                    'X04': 'color',
                    'X05': 'size',
                    'X06': 'qty',
                    'X07': 'qty_ok',
                    'X08': 'qty_recheck',
                    'X09': 'qty_recheck_ok',
                    'X10': 'qty_c',
                    'XC': 'comments',
                    # Add more mappings as needed
                }
            },
         
            'T52_ProductItem': {
                'sync': True,
                'columns': None,  # None means all columns
                'condition': None, #"X02 > '2025-03-31'",  # X02 is the datetime column
                'sync_mode': 'incremental',  # 'full' or 'incremental'
                'timestamp_column': None ,  # Column for incremental sync tracking
                'primary_key': 'ID',  # Primary key for upsert operations
                'column_mapping': {
                    'X14': 'style_no',
                    'X15': 'style_text',
                    'X16': 'brand',
                    'X17' : 'description'
                }
            },
            'T58_InLineData': {
                'sync': True,
                'columns': None,  # None means all columns
                'condition': None, #"X02 > '2025-03-31'",  # X02 is the datetime column
                'sync_mode': 'incremental',  # 'full' or 'incremental'
                'timestamp_column': 'X02',  # Column for incremental sync tracking
                'primary_key': 'ID',  # Primary key for upsert operations
                'column_mapping': {  # Map MSSQL columns to MariaDB columns 
                    'X01': 'line',
                    'X02': 'date',  # datetime column
                    'X03': 'process_no', 
                    'X04': 'color',   
                    'X05': 'qty',
                    'X06': 'qty_ok',
                    'X08': 'item_id',
                    'X07': 'comments'  # nvarchar field at end
                }
            }, 
            'T59_TransInLine': {
                'sync': True,
                'columns': None,  # None means all columns
                'condition': None,
                'sync_mode': 'incremental',  # 'full' or 'incremental'
                'timestamp_column': None,  # Column for incremental sync tracking
                'primary_key': 'ID',  # Primary key for upsert operations
                'column_mapping': {  # Map MSSQL columns to MariaDB columns 
                    'item': 'item_id',
                    'Process': 'process_id',  # Note: uppercase P in MSSQL
                    'MajorViet': 'major_viet',
                    'MajorJpn': 'major_jpn', 
                    'ProViet': 'process_viet',
                    'ProJpn': 'process_jpn'
                }
            }, 
        }
    
    def get_table_sync_config(self) -> Dict[str, Any]:
        """Get table synchronization configuration"""
        return self.table_sync_config.copy()
    
    def should_sync_table(self, table_name: str) -> bool:
        """Check if table should be synced"""
        table_config = self.table_sync_config.get(table_name, {})
        return table_config.get('sync', False)
    
    def get_table_columns(self, table_name: str) -> Optional[list]:
        """Get column filters for a table"""
        table_config = self.table_sync_config.get(table_name, {})
        return table_config.get('columns')
    
    def get_table_condition(self, table_name: str) -> Optional[str]:
        """Get WHERE condition for a table"""
        table_config = self.table_sync_config.get(table_name, {})
        return table_config.get('condition')
    
    def get_sync_mode(self, table_name: str) -> str:
        """Get sync mode for a table (full/incremental)"""
        table_config = self.table_sync_config.get(table_name, {})
        return table_config.get('sync_mode', 'full')
    
    def get_timestamp_column(self, table_name: str) -> Optional[str]:
        """Get timestamp column for incremental sync"""
        table_config = self.table_sync_config.get(table_name, {})
        return table_config.get('timestamp_column')
    
    def get_primary_key(self, table_name: str) -> str:
        """Get primary key column for upsert operations"""
        table_config = self.table_sync_config.get(table_name, {})
        return table_config.get('primary_key', 'ID')
    
    def get_column_mapping(self, table_name: str) -> Optional[Dict[str, str]]:
        """Get column mapping for a table (MSSQL -> MariaDB)"""
        table_config = self.table_sync_config.get(table_name, {})
        return table_config.get('column_mapping')
    
    def map_column_name(self, table_name: str, original_name: str) -> str:
        """Map original MSSQL column name to MariaDB column name"""
        column_mapping = self.get_column_mapping(table_name)
        if column_mapping and original_name in column_mapping:
            return column_mapping[original_name]
        return original_name
    
    def get_mapped_columns(self, table_name: str, original_columns: List[str]) -> List[str]:
        """Apply column mapping to a list of column names"""
        return [self.map_column_name(table_name, col) for col in original_columns]