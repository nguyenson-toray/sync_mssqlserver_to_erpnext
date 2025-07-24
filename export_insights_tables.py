#!/usr/bin/env python3
"""
Export table names starting with 'tabInsights' to file
"""

import mysql.connector
from mysql.connector import Error as MySQLError
import logging
import sys
import os

# Add the current directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import DatabaseConfig

def export_insights_tables():
    """Export all table names starting with 'tabInsights' to file"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize config
        config = DatabaseConfig()
        mariadb_config = config.get_mariadb_config()
        
        # Connect to MariaDB
        logger.info("Connecting to MariaDB...")
        conn = mysql.connector.connect(**mariadb_config)
        cursor = conn.cursor()
        
        # Query for tables starting with 'tabInsights'
        query = "SHOW TABLES LIKE 'tabInsights%'"
        logger.info(f"Executing query: {query}")
        cursor.execute(query)
        
        # Fetch all results
        results = cursor.fetchall()
        table_names = [row[0] for row in results]
        
        logger.info(f"Found {len(table_names)} tables starting with 'tabInsights'")
        
        # Export to file
        output_file = "/home/sonnt/frappe-bench/sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/insights_manual_export_import/insights_table.txt"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            for table_name in table_names:
                f.write(f"{table_name}\n")
                logger.info(f"Exported: {table_name}")
        
        logger.info(f"Successfully exported {len(table_names)} table names to {output_file}")
        
        # Close connections
        cursor.close()
        conn.close()
        
        return True
        
    except MySQLError as e:
        logger.error(f"MySQL error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = export_insights_tables()
    sys.exit(0 if success else 1)