"""
Data type conversion utilities for MSSQL to MariaDB migration
"""

def convert_datatype(sql_server_type: str) -> str:
    """
    Convert SQL Server data types to MariaDB equivalents
    
    Args:
        sql_server_type: SQL Server column type (e.g., 'varchar(50)', 'int')
        
    Returns:
        Equivalent MariaDB data type
    """
    type_mapping = {
        'int': 'INT',
        'bigint': 'BIGINT',
        'smallint': 'SMALLINT',
        'tinyint': 'TINYINT',
        'bit': 'BOOLEAN',
        'decimal': 'DECIMAL',
        'numeric': 'DECIMAL',
        'money': 'DECIMAL(19,4)',
        'smallmoney': 'DECIMAL(10,4)',
        'float': 'FLOAT',
        'real': 'REAL',
        'datetime': 'DATETIME',
        'datetime2': 'DATETIME',
        'smalldatetime': 'DATETIME',
        'date': 'DATE',
        'time': 'TIME',
        'timestamp': 'TIMESTAMP',
        'char': 'CHAR',
        'varchar': 'VARCHAR',
        'nchar': 'CHAR',
        'nvarchar': 'VARCHAR',
        'text': 'TEXT',
        'ntext': 'TEXT',
        'image': 'LONGBLOB',
        'varbinary': 'VARBINARY',
        'binary': 'BINARY',
        'uniqueidentifier': 'VARCHAR(36)',
        'xml': 'TEXT'
    }
    
    # Handle types with parameters (e.g., varchar(50))
    base_type = sql_server_type.split('(')[0].lower()
    
    if base_type in type_mapping:
        if '(' in sql_server_type and base_type in ['varchar', 'nvarchar', 'char', 'nchar', 'varbinary', 'binary']:
            # Keep the size parameter for these types
            size_part = sql_server_type.split('(')[1]
            if size_part == 'max)' or size_part == '-1)':
                if base_type in ['varchar', 'nvarchar']:
                    return 'TEXT'
                elif base_type in ['varbinary']:
                    return 'LONGBLOB'
            return f"{type_mapping[base_type]}({size_part}"
        elif '(' in sql_server_type and base_type in ['decimal', 'numeric']:
            # Keep precision and scale for decimal types
            precision_scale = sql_server_type.split('(')[1]
            return f"DECIMAL({precision_scale}"
        else:
            return type_mapping[base_type]
    
    # Default fallback
    return 'TEXT'


def clean_value(value):
    """
    Clean and prepare value for MariaDB insertion
    
    Args:
        value: Raw value from MSSQL
        
    Returns:
        Cleaned value ready for insertion
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        # Remove null bytes and control characters
        value = value.replace('\x00', '').replace('\r', '').replace('\n', ' ')
        # Trim whitespace
        value = value.strip()
        
        # Handle MSSQL datetime format conversion
        if value and _is_mssql_datetime_format(value):
            return _convert_mssql_datetime(value)
        
        # Return None for empty strings if needed
        return value if value else None
    
    return value


def _is_mssql_datetime_format(value: str) -> bool:
    """Check if value matches MSSQL datetime format like 'Apr  1 2025 12:00AM'"""
    import re
    # Pattern: Month Day Year Hour:MinuteAM/PM
    pattern = r'^[A-Za-z]{3}\s+\d{1,2}\s+\d{4}\s+\d{1,2}:\d{2}[AP]M$'
    return bool(re.match(pattern, value))


def _convert_mssql_datetime(value: str) -> str:
    """Convert MSSQL datetime format to MariaDB format"""
    try:
        from datetime import datetime
        
        # Parse MSSQL format: 'Apr  1 2025 12:00AM'
        # Note: there might be extra spaces between month and day
        cleaned_value = ' '.join(value.split())  # Remove extra spaces
        dt = datetime.strptime(cleaned_value, '%b %d %Y %I:%M%p')
        
        # Return in MariaDB format: 'YYYY-MM-DD HH:MM:SS'
        return dt.strftime('%Y-%m-%d %H:%M:%S')
        
    except ValueError as e:
        # If parsing fails, return the original value and let MariaDB handle it
        print(f"Warning: Could not convert datetime '{value}': {e}")
        return value