#!/usr/bin/env python3
"""
Optimized MSSQL to MariaDB Data Synchronization Tool
Consolidates and improves upon existing migration scripts
"""

import subprocess
import mysql.connector
from mysql.connector import Error as MySQLError
import logging
import sys
import os
from datetime import datetime
from typing import List, Tuple
import time

from config import DatabaseConfig
from data_types import convert_datatype, clean_value
from sync_tracker import SyncTracker

class DatabaseSyncer:
    """Main database synchronization class"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.sync_tracker = SyncTracker()
        self.mariadb_conn = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = logging.DEBUG if os.getenv('DEBUG') else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('sync.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_mariadb(self) -> bool:
        """Establish MariaDB connection"""
        try:
            mariadb_config = self.config.get_mariadb_config()
            
            # Connect without database first to create it
            temp_config = mariadb_config.copy()
            del temp_config['database']
            
            temp_conn = mysql.connector.connect(**temp_config)
            cursor = temp_conn.cursor()
            
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{mariadb_config['database']}`")
            cursor.close()
            temp_conn.close()
            
            # Connect to the target database
            self.mariadb_conn = mysql.connector.connect(**mariadb_config)
            self.logger.info("Connected to MariaDB successfully")
            return True
            
        except MySQLError as e:
            self.logger.error(f"MariaDB connection failed: {e}")
            return False
    
    def execute_mssql_query(self, query: str) -> List[List[str]]:
        """Execute query on MSSQL using available client and return results"""
        try:
            cmd = self.config.mssql_command
            client_type = self.config.mssql_client_type
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=f"{query}\nGO\n")
            
            if process.returncode != 0:
                self.logger.error(f"MSSQL query failed: {stderr}")
                return []
            
            return self._parse_query_output(stdout, client_type)
            
        except Exception as e:
            self.logger.error(f"Error executing MSSQL query: {e}")
            return []
    
    def _parse_query_output(self, stdout: str, client_type: str) -> List[List[str]]:
        """Parse SQL client output into structured data"""
        lines = stdout.strip().split('\n')
        results = []
        
        skip_patterns = ['locale is', 'charset is', 'using default charset', '---', '1>', '2>', 'COLUMN_NAME', 'Setting Production']
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
                
            # Skip specific patterns
            if any(pattern in line for pattern in skip_patterns):
                continue
                
            # Skip lines that start with "(" followed by numbers (like "(72 rows affected)")
            if line.startswith('(') and ('rows affected' in line or 'row affected' in line):
                continue
                
            # Parse based on client type
            if client_type == 'sqlcmd':
                values = [val.strip() if val.strip() != 'NULL' else None for val in line.split()]
            else:
                # tsql parsing - split by tab first, then whitespace
                if '\t' in line:
                    values = [val.strip() if val.strip() != 'NULL' else None for val in line.split('\t')]
                else:
                    values = [val.strip() if val.strip() != 'NULL' else None for val in line.split()]
                
                # Don't remove empty values - they represent actual columns with empty data
                # values = [val for val in values if val is not None]
            
            # Accept rows with any number of values (including single values like COUNT results)
            if values:
                results.append(values)
        
        return results
    
    def get_table_list(self) -> List[str]:
        """Get list of tables to sync from configuration"""
        table_config = self.config.get_table_sync_config()
        tables = [name for name, config in table_config.items() if config.get('sync', False)]
        self.logger.info(f"Using configured tables: {len(tables)} tables")
        return tables
    
    def get_table_structure(self, table_name: str) -> List[Tuple[str, str]]:
        """Get table structure from MSSQL with optional column filtering"""
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE + 
               CASE 
                   WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL 
                   THEN '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) + ')'
                   WHEN NUMERIC_PRECISION IS NOT NULL AND NUMERIC_SCALE IS NOT NULL
                   THEN '(' + CAST(NUMERIC_PRECISION AS VARCHAR) + ',' + CAST(NUMERIC_SCALE AS VARCHAR) + ')'
                   ELSE ''
               END as FULL_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        
        results = self.execute_mssql_query(query)
        columns = []
        
        # Get column filters for this table
        column_filters = self.config.get_table_columns(table_name)
        
        for row in results:
            if len(row) >= 2 and row[0]:
                original_col_name = str(row[0]).strip()
                clean_col_name = self._clean_column_name(table_name, original_col_name)
                col_type = str(row[1]).strip()
                
                # Apply column filter if specified (check against original names)
                if column_filters:
                    # Check both original and mapped names
                    if (original_col_name not in column_filters and 
                        clean_col_name not in column_filters and
                        not any(original_col_name.lower() == cf.lower() for cf in column_filters) and
                        not any(clean_col_name.lower() == cf.lower() for cf in column_filters)):
                        continue
                
                if clean_col_name:
                    columns.append((clean_col_name, col_type))
        
        if column_filters:
            self.logger.info(f"Found {len(columns)} filtered columns for table {table_name}: {column_filters}")
        else:
            self.logger.info(f"Found {len(columns)} columns for table {table_name}")
        return columns
    
    def _clean_column_name(self, table_name: str, col_name: str) -> str:
        """Clean and normalize column names with mapping support"""
        # Remove brackets and clean
        clean_name = col_name.replace('[', '').replace(']', '').strip()
        
        # Apply column mapping if configured
        mapped_name = self.config.map_column_name(table_name, clean_name)
        if mapped_name != clean_name:
            return mapped_name
        
        # Handle special cases for unmapped columns
        if clean_name and clean_name[0].isdigit():
            return f"col_{clean_name}"
        
        return clean_name
    
    def create_mariadb_table(self, table_name: str, columns: List[Tuple[str, str]]) -> bool:
        """Create table in MariaDB with converted data types"""
        try:
            cursor = self.mariadb_conn.cursor()
            sync_mode = self.config.get_sync_mode(table_name)
            
            # For full sync, drop and recreate table
            if sync_mode == 'full':
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            else:
                # For incremental sync, check if table exists
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if cursor.fetchone():
                    self.logger.info(f"Table {table_name} exists, using incremental sync")
                    cursor.close()
                    return True  # Table exists, no need to recreate
            
            # Build CREATE TABLE statement
            column_definitions = []
            primary_key = None
            
            for col_name, col_type in columns:
                mariadb_type = convert_datatype(col_type)
                # Validate column name and type
                if col_name and mariadb_type:
                    # Handle ID column as auto-increment primary key
                    if col_name.upper() == 'ID':
                        column_definitions.append(f"`{col_name}` {mariadb_type} AUTO_INCREMENT")
                        primary_key = col_name
                    else:
                        column_definitions.append(f"`{col_name}` {mariadb_type}")
                else:
                    self.logger.warning(f"Skipping invalid column: {col_name} {col_type}")
            
            if not column_definitions:
                self.logger.error(f"No valid column definitions for table {table_name}")
                return False
            
            # Add primary key constraint if ID column exists
            if primary_key:
                column_definitions.append(f"PRIMARY KEY (`{primary_key}`)")
            
            create_sql = f"""
            CREATE TABLE `{table_name}` (
                {', '.join(column_definitions)}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            self.logger.info(f"CREATE TABLE SQL: {create_sql}")
            cursor.execute(create_sql)
            cursor.close()
            
            mode_msg = "(full sync)" if sync_mode == 'full' else "(incremental sync)"
            self.logger.info(f"Created table {table_name} with {len(columns)} columns {mode_msg}")
            return True
            
        except MySQLError as e:
            self.logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get total row count for a table from MSSQL"""
        condition = self._build_sync_condition(table_name)
        
        if condition:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE {condition}"
        else:
            query = f"SELECT COUNT(*) FROM {table_name}"
        
        results = self.execute_mssql_query(query)
        
        if results and results[0]:
            try:
                return int(results[0][0])
            except (ValueError, IndexError):
                pass
        
        return 0
    
    def sync_table_data(self, table_name: str, columns: List[Tuple[str, str]]) -> bool:
        """Sync data for a single table using batch processing"""
        try:
            sync_mode = self.config.get_sync_mode(table_name)
            total_rows = self.get_table_row_count(table_name)
            batch_size = self.config.sync_config['batch_size']
            
            # Prepare column mappings
            original_columns, renamed_columns = self._get_column_mappings(table_name, columns)
            
            # Choose sync strategy
            if sync_mode == 'incremental':
                sql_template = self._build_upsert_sql(table_name, renamed_columns)
                mode_msg = "(incremental)"
            else:
                sql_template = self._build_insert_sql(table_name, renamed_columns)
                mode_msg = "(full)"
            
            self.logger.info(f"Table {table_name}: Syncing {total_rows or 'unknown'} rows {mode_msg}")
            
            cursor = self.mariadb_conn.cursor()
            offset = 0
            synced_rows = 0
            
            while True:
                batch_data = self._fetch_batch_data(table_name, original_columns, offset, batch_size)
                
                if not batch_data:
                    break
                
                clean_batch = self._clean_batch_data(batch_data, len(renamed_columns))
                
                if clean_batch:
                    cursor.executemany(sql_template, clean_batch)
                    self.mariadb_conn.commit()
                    synced_rows += len(clean_batch)
                    
                    self._log_progress(table_name, synced_rows, total_rows)
                
                offset += batch_size
                
                if len(batch_data) < batch_size:
                    break
                
                time.sleep(0.1)  # Rate limiting
            
            cursor.close()
            
            # Update last sync timestamp for incremental sync
            if sync_mode == 'incremental' and synced_rows > 0:
                self._update_last_sync_timestamp(table_name)
            
            self.logger.info(f"Table {table_name}: Sync completed ({synced_rows} rows)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sync table {table_name}: {e}")
            return False
    
    def _get_column_mappings(self, table_name: str, columns: List[Tuple[str, str]]) -> Tuple[List[str], List[str]]:
        """Get original and renamed column mappings"""
        original_columns = []
        renamed_columns = []
        column_mapping = self.config.get_column_mapping(table_name)
        
        # Create reverse mapping (MariaDB -> MSSQL) for query building
        reverse_mapping = {}
        if column_mapping:
            reverse_mapping = {v: k for k, v in column_mapping.items()}
        
        for col_name, _ in columns:
            # Get original column name for MSSQL queries
            if col_name in reverse_mapping:
                original_columns.append(reverse_mapping[col_name])
            else:
                original_columns.append(col_name)
            
            # MariaDB column name (already mapped)
            renamed_columns.append(col_name)
        
        return original_columns, renamed_columns
    
    def _build_insert_sql(self, table_name: str, columns: List[str]) -> str:
        """Build INSERT SQL statement"""
        placeholders = ', '.join(['%s'] * len(columns))
        return f"INSERT INTO `{table_name}` (`{'`, `'.join(columns)}`) VALUES ({placeholders})"
    
    def _build_upsert_sql(self, table_name: str, columns: List[str]) -> str:
        """Build INSERT...ON DUPLICATE KEY UPDATE SQL statement"""
        placeholders = ', '.join(['%s'] * len(columns))
        primary_key = self.config.get_primary_key(table_name)
        
        # Build update clause (exclude primary key)
        update_columns = [col for col in columns if col != primary_key]
        update_clause = ', '.join([f"`{col}` = VALUES(`{col}`)" for col in update_columns])
        
        return f"""
        INSERT INTO `{table_name}` (`{'`, `'.join(columns)}`) 
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause}
        """
    
    def _update_last_sync_timestamp(self, table_name: str):
        """Update last sync timestamp for incremental sync"""
        timestamp_column = self.config.get_timestamp_column(table_name)
        if not timestamp_column:
            return
        
        try:
            # Get the latest timestamp from the synced data
            query = f"SELECT MAX({timestamp_column}) FROM {table_name}"
            results = self.execute_mssql_query(query)
            
            if results and results[0] and results[0][0]:
                latest_timestamp = results[0][0]
                self.sync_tracker.set_last_sync(table_name, latest_timestamp)
                self.logger.info(f"Updated last sync timestamp for {table_name}: {latest_timestamp}")
        except Exception as e:
            self.logger.warning(f"Could not update last sync timestamp for {table_name}: {e}")
    
    def _fetch_batch_data(self, table_name: str, columns: List[str], offset: int, batch_size: int) -> List[List[str]]:
        """Fetch batch of data from MSSQL with column filtering"""
        # Build SELECT clause with proper column mapping
        original_columns, _ = self._get_column_mappings(table_name, [(col, '') for col in columns])
        select_columns = ', '.join(original_columns)
        
        base_query = f"SELECT {select_columns} FROM {table_name}"
        
        if offset == 0:
            query = f"SELECT TOP {batch_size} {select_columns} FROM {table_name}"
            query = self._apply_sync_condition(table_name, query)
        else:
            filtered_query = self._apply_sync_condition(table_name, base_query)
            primary_key = self.config.get_primary_key(table_name)
            query = f"{filtered_query} ORDER BY {primary_key} OFFSET {offset} ROWS FETCH NEXT {batch_size} ROWS ONLY"
        
        return self.execute_mssql_query(query)
    
    def _build_sync_condition(self, table_name: str) -> str:
        """Build sync condition based on sync mode and configuration"""
        sync_mode = self.config.get_sync_mode(table_name)
        base_condition = self.config.get_table_condition(table_name)
        
        if sync_mode == 'incremental':
            timestamp_column = self.config.get_timestamp_column(table_name)
            if timestamp_column:
                return self.sync_tracker.get_incremental_condition(
                    table_name, timestamp_column, base_condition
                )
        
        return base_condition or ""
    
    def _apply_sync_condition(self, table_name: str, base_query: str) -> str:
        """Apply sync condition to query"""
        condition = self._build_sync_condition(table_name)
        
        if condition:
            if 'WHERE' in base_query.upper():
                return f"{base_query} AND {condition}"
            else:
                return f"{base_query} WHERE {condition}"
        
        return base_query
    
    def _clean_batch_data(self, batch_data: List[List[str]], expected_cols: int) -> List[List]:
        """Clean and validate batch data"""
        clean_batch = []
        for row in batch_data:
            clean_row = [clean_value(val) for val in row]
            if len(clean_row) == expected_cols:
                clean_batch.append(clean_row)
        return clean_batch
    
    def _log_progress(self, table_name: str, synced_rows: int, total_rows: int):
        """Log sync progress"""
        if total_rows > 0:
            progress = (synced_rows / total_rows) * 100
            self.logger.info(f"Table {table_name}: {synced_rows}/{total_rows} rows ({progress:.1f}%)")
        else:
            self.logger.info(f"Table {table_name}: {synced_rows} rows synced")
    
    def sync_table(self, table_name: str) -> bool:
        """Sync a single table (structure + data)"""
        self.logger.info(f"Starting sync for table: {table_name}")
        
        # Check if table should be synced
        if not self.config.should_sync_table(table_name):
            self.logger.info(f"Skipping table {table_name} (not in sync configuration)")
            return True
        
        # Get table structure
        columns = self.get_table_structure(table_name)
        if not columns:
            self.logger.error(f"Could not get structure for table {table_name}")
            return False
        
        # Create table in MariaDB
        if not self.create_mariadb_table(table_name, columns):
            return False
        
        # Sync data
        return self.sync_table_data(table_name, columns)
    
    def force_full_sync(self, table_name: str = None):
        """Force full sync by clearing last sync timestamps"""
        if table_name:
            self.sync_tracker.clear_last_sync(table_name)
            self.logger.info(f"Cleared last sync timestamp for {table_name} - next sync will be full")
        else:
            # Clear all timestamps
            for table in self.config.get_table_sync_config().keys():
                self.sync_tracker.clear_last_sync(table)
            self.logger.info("Cleared all sync timestamps - next sync will be full for all tables")
    
    def run_sync(self, force_full: bool = False) -> bool:
        """Run complete database synchronization"""
        start_time = datetime.now()
        
        if force_full:
            self.force_full_sync()
        
        self.logger.info("=== Starting Database Synchronization ===")
        
        # Connect to MariaDB
        if not self.connect_mariadb():
            return False
        
        try:
            # Get tables to sync
            tables = self.get_table_list()
            
            if not tables:
                self.logger.error("No tables found to sync")
                return False
            
            success_count = 0
            total_tables = len(tables)
            
            # Sync each table
            for i, table_name in enumerate(tables, 1):
                self.logger.info(f"Processing table {i}/{total_tables}: {table_name}")
                
                if self.sync_table(table_name):
                    success_count += 1
                else:
                    self.logger.error(f"Failed to sync table: {table_name}")
            
            # Summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info("=== Synchronization Summary ===")
            self.logger.info(f"Total tables: {total_tables}")
            self.logger.info(f"Successful: {success_count}")
            self.logger.info(f"Failed: {total_tables - success_count}")
            self.logger.info(f"Duration: {duration}")
            
            return success_count == total_tables
            
        finally:
            if self.mariadb_conn:
                self.mariadb_conn.close()
                self.logger.info("MariaDB connection closed")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MSSQL to MariaDB Sync Tool')
    parser.add_argument('--force-full', action='store_true', 
                       help='Force full sync (ignore incremental timestamps)')
    parser.add_argument('--table', type=str, 
                       help='Sync specific table only')
    
    args = parser.parse_args()
    syncer = DatabaseSyncer()
    
    try:
        if args.table:
            # Sync specific table
            if syncer.connect_mariadb():
                success = syncer.sync_table(args.table)
                syncer.mariadb_conn.close()
            else:
                success = False
        else:
            # Sync all configured tables
            success = syncer.run_sync(force_full=args.force_full)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        syncer.logger.info("Synchronization interrupted by user")
        sys.exit(1)
    except Exception as e:
        syncer.logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()