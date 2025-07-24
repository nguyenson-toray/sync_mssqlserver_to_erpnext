#!/usr/bin/env python3
"""
Export MariaDB Table Structure After Sync
Exports table structures to JSON and SQL format for documentation and analysis
"""

import mysql.connector
from mysql.connector import Error as MySQLError
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import argparse

from config import DatabaseConfig

class TableStructureExporter:
    """Export MariaDB table structures after sync"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.mariadb_conn = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = logging.DEBUG if os.getenv('DEBUG') else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('export_structure.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_mariadb(self) -> bool:
        """Establish MariaDB connection"""
        try:
            mariadb_config = self.config.get_mariadb_config()
            self.mariadb_conn = mysql.connector.connect(**mariadb_config)
            self.logger.info("Connected to MariaDB successfully")
            return True
            
        except MySQLError as e:
            self.logger.error(f"MariaDB connection failed: {e}")
            return False
    
    def get_synced_tables(self) -> List[str]:
        """Get list of tables that have been synced"""
        try:
            cursor = self.mariadb_conn.cursor()
            cursor.execute("SHOW TABLES")
            
            all_tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            # Filter only configured sync tables that exist in MariaDB
            table_config = self.config.get_table_sync_config()
            synced_tables = []
            
            for table_name in all_tables:
                if table_name in table_config and table_config[table_name].get('sync', False):
                    synced_tables.append(table_name)
            
            self.logger.info(f"Found {len(synced_tables)} synced tables: {synced_tables}")
            return synced_tables
            
        except MySQLError as e:
            self.logger.error(f"Failed to get table list: {e}")
            return []
    
    def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """Get detailed table structure information"""
        try:
            cursor = self.mariadb_conn.cursor(dictionary=True)
            
            # Get column information
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    COLUMN_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    COLUMN_KEY,
                    EXTRA,
                    COLUMN_COMMENT,
                    ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            
            # Get table information
            cursor.execute(f"""
                SELECT 
                    TABLE_COMMENT,
                    ENGINE,
                    TABLE_COLLATION,
                    CREATE_TIME,
                    UPDATE_TIME
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}'
            """)
            
            table_info = cursor.fetchone()
            
            # Get indexes
            cursor.execute(f"SHOW INDEX FROM `{table_name}`")
            indexes_raw = cursor.fetchall()
            
            # Process indexes
            indexes = {}
            for idx in indexes_raw:
                idx_name = idx['Key_name']
                if idx_name not in indexes:
                    indexes[idx_name] = {
                        'unique': not idx['Non_unique'],
                        'type': idx['Index_type'],
                        'columns': []
                    }
                indexes[idx_name]['columns'].append({
                    'column': idx['Column_name'],
                    'sequence': idx['Seq_in_index']
                })
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as row_count FROM `{table_name}`")
            row_count = cursor.fetchone()['row_count']
            
            # Get table size
            cursor.execute(f"""
                SELECT 
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.TABLES 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table_name}'
            """)
            size_info = cursor.fetchone()
            
            cursor.close()
            
            # Get sync configuration
            table_config = self.config.get_table_sync_config().get(table_name, {})
            
            return {
                'table_name': table_name,
                'table_info': {
                    'comment': table_info['TABLE_COMMENT'] if table_info else None,
                    'engine': table_info['ENGINE'] if table_info else None,
                    'collation': table_info['TABLE_COLLATION'] if table_info else None,
                    'created': table_info['CREATE_TIME'].isoformat() if table_info and table_info['CREATE_TIME'] else None,
                    'updated': table_info['UPDATE_TIME'].isoformat() if table_info and table_info['UPDATE_TIME'] else None,
                    'row_count': row_count,
                    'size_mb': float(size_info['size_mb']) if size_info and size_info['size_mb'] else 0
                },
                'columns': columns,
                'indexes': indexes,
                'sync_config': {
                    'sync_mode': table_config.get('sync_mode', 'full'),
                    'timestamp_column': table_config.get('timestamp_column'),
                    'primary_key': table_config.get('primary_key'),
                    'column_mapping': table_config.get('column_mapping', {}),
                    'condition': table_config.get('condition'),
                    'columns_filter': table_config.get('columns')
                }
            }
            
        except MySQLError as e:
            self.logger.error(f"Failed to get structure for table {table_name}: {e}")
            return {}
    
    def generate_create_table_sql(self, table_structure: Dict[str, Any]) -> str:
        """Generate CREATE TABLE SQL from structure"""
        table_name = table_structure['table_name']
        columns = table_structure['columns']
        indexes = table_structure['indexes']
        
        sql_parts = [f"CREATE TABLE `{table_name}` ("]
        
        # Add columns
        column_definitions = []
        for col in columns:
            col_def = f"  `{col['COLUMN_NAME']}` {col['COLUMN_TYPE']}"
            
            if col['IS_NULLABLE'] == 'NO':
                col_def += " NOT NULL"
            
            if col['COLUMN_DEFAULT'] is not None:
                if col['DATA_TYPE'] in ['varchar', 'char', 'text', 'datetime', 'timestamp']:
                    col_def += f" DEFAULT '{col['COLUMN_DEFAULT']}'"
                else:
                    col_def += f" DEFAULT {col['COLUMN_DEFAULT']}"
            
            if col['EXTRA']:
                col_def += f" {col['EXTRA']}"
            
            if col['COLUMN_COMMENT']:
                col_def += f" COMMENT '{col['COLUMN_COMMENT']}'"
                
            column_definitions.append(col_def)
        
        sql_parts.extend(column_definitions)
        
        # Add primary key
        primary_key = None
        for idx_name, idx_info in indexes.items():
            if idx_name == 'PRIMARY':
                pk_columns = [col['column'] for col in sorted(idx_info['columns'], key=lambda x: x['sequence'])]
                primary_key = f"  PRIMARY KEY (`{'`, `'.join(pk_columns)}`)"
                break
        
        if primary_key:
            sql_parts.append(primary_key)
        
        # Add other indexes
        for idx_name, idx_info in indexes.items():
            if idx_name != 'PRIMARY':
                idx_columns = [col['column'] for col in sorted(idx_info['columns'], key=lambda x: x['sequence'])]
                if idx_info['unique']:
                    idx_def = f"  UNIQUE KEY `{idx_name}` (`{'`, `'.join(idx_columns)}`)"
                else:
                    idx_def = f"  KEY `{idx_name}` (`{'`, `'.join(idx_columns)}`)"
                sql_parts.append(idx_def)
        
        # Table options
        table_info = table_structure['table_info']
        sql_parts.append(f") ENGINE={table_info.get('engine', 'InnoDB')} DEFAULT CHARSET=utf8mb4 COLLATE={table_info.get('collation', 'utf8mb4_unicode_ci')};")
        
        return ',\n'.join(sql_parts[:-1]) + '\n' + sql_parts[-1]
    
    def export_to_json(self, tables_structure: Dict[str, Any], output_file: str = None):
        """Export table structures to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"mariadb_table_structures_{timestamp}.json"
        
        export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'database': self.config.get_mariadb_config()['database'],
                'total_tables': len(tables_structure),
                'exporter_version': '1.0'
            },
            'tables': tables_structure
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Table structures exported to JSON: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            return None
    
    def export_to_sql(self, tables_structure: Dict[str, Any], output_file: str = None):
        """Export table structures to SQL file"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"mariadb_table_structures_{timestamp}.sql"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"-- MariaDB Table Structures Export\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Database: {self.config.get_mariadb_config()['database']}\n")
                f.write(f"-- Total Tables: {len(tables_structure)}\n\n")
                
                f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
                
                for table_name, structure in tables_structure.items():
                    f.write(f"-- ========================================\n")
                    f.write(f"-- Table: {table_name}\n")
                    f.write(f"-- Sync Mode: {structure['sync_config']['sync_mode']}\n")
                    f.write(f"-- Row Count: {structure['table_info']['row_count']}\n")
                    f.write(f"-- Size: {structure['table_info']['size_mb']} MB\n")
                    f.write(f"-- ========================================\n\n")
                    
                    f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n\n")
                    f.write(self.generate_create_table_sql(structure))
                    f.write("\n\n")
                
                f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            
            self.logger.info(f"Table structures exported to SQL: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Failed to export SQL: {e}")
            return None
    
    def export_summary_report(self, tables_structure: Dict[str, Any], output_file: str = None):
        """Generate summary report"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"sync_summary_report_{timestamp}.md"
        
        try:
            total_rows = sum(t['table_info']['row_count'] for t in tables_structure.values())
            total_size = sum(t['table_info']['size_mb'] for t in tables_structure.values())
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# MariaDB Sync Summary Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**Database:** {self.config.get_mariadb_config()['database']}\n\n")
                f.write(f"## Overview\n\n")
                f.write(f"- **Total Tables:** {len(tables_structure)}\n")
                f.write(f"- **Total Rows:** {total_rows:,}\n")
                f.write(f"- **Total Size:** {total_size:.2f} MB\n\n")
                
                f.write(f"## Table Details\n\n")
                f.write(f"| Table | Sync Mode | Rows | Size (MB) | Columns | Primary Key |\n")
                f.write(f"|-------|-----------|------|-----------|---------|-------------|\n")
                
                for table_name, structure in sorted(tables_structure.items()):
                    sync_mode = structure['sync_config']['sync_mode']
                    row_count = structure['table_info']['row_count']
                    size_mb = structure['table_info']['size_mb']
                    col_count = len(structure['columns'])
                    pk = structure['sync_config']['primary_key'] or 'N/A'
                    
                    f.write(f"| {table_name} | {sync_mode} | {row_count:,} | {size_mb:.2f} | {col_count} | {pk} |\n")
                
                f.write(f"\n## Sync Configuration\n\n")
                for table_name, structure in sorted(tables_structure.items()):
                    config = structure['sync_config']
                    f.write(f"### {table_name}\n\n")
                    f.write(f"- **Sync Mode:** {config['sync_mode']}\n")
                    if config['timestamp_column']:
                        f.write(f"- **Timestamp Column:** {config['timestamp_column']}\n")
                    if config['primary_key']:
                        f.write(f"- **Primary Key:** {config['primary_key']}\n")
                    if config['condition']:
                        f.write(f"- **Condition:** `{config['condition']}`\n")
                    if config['column_mapping']:
                        f.write(f"- **Column Mapping:** {len(config['column_mapping'])} mappings\n")
                    f.write(f"\n")
            
            self.logger.info(f"Summary report exported: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Failed to export summary report: {e}")
            return None
    
    def export_all(self, output_format: str = "all", specific_tables: List[str] = None) -> Dict[str, str]:
        """Export table structures in specified format(s)"""
        if not self.connect_mariadb():
            return {}
        
        try:
            # Get tables to export
            if specific_tables:
                tables = specific_tables
                self.logger.info(f"Exporting specific tables: {tables}")
            else:
                tables = self.get_synced_tables()
                if not tables:
                    self.logger.error("No synced tables found")
                    return {}
            
            # Get structures
            tables_structure = {}
            for table_name in tables:
                self.logger.info(f"Getting structure for table: {table_name}")
                structure = self.get_table_structure(table_name)
                if structure:
                    tables_structure[table_name] = structure
            
            if not tables_structure:
                self.logger.error("No table structures retrieved")
                return {}
            
            # Export in requested formats
            output_files = {}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if output_format in ["all", "json"]:
                json_file = self.export_to_json(tables_structure, f"mariadb_structures_{timestamp}.json")
                if json_file:
                    output_files['json'] = json_file
            
            if output_format in ["all", "sql"]:
                sql_file = self.export_to_sql(tables_structure, f"mariadb_structures_{timestamp}.sql")
                if sql_file:
                    output_files['sql'] = sql_file
            
            if output_format in ["all", "report"]:
                report_file = self.export_summary_report(tables_structure, f"sync_report_{timestamp}.md")
                if report_file:
                    output_files['report'] = report_file
            
            # Summary
            self.logger.info("=== Export Summary ===")
            self.logger.info(f"Tables exported: {len(tables_structure)}")
            for format_type, file_path in output_files.items():
                self.logger.info(f"{format_type.upper()}: {file_path}")
            
            return output_files
            
        finally:
            if self.mariadb_conn:
                self.mariadb_conn.close()
                self.logger.info("MariaDB connection closed")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Export MariaDB Table Structures After Sync')
    parser.add_argument('--format', choices=['json', 'sql', 'report', 'all'], 
                       default='all', help='Export format (default: all)')
    parser.add_argument('--tables', nargs='+', 
                       help='Specific tables to export (default: all synced tables)')
    parser.add_argument('--output-prefix', type=str,
                       help='Output file prefix')
    
    args = parser.parse_args()
    
    exporter = TableStructureExporter()
    
    try:
        output_files = exporter.export_all(
            output_format=args.format,
            specific_tables=args.tables
        )
        
        if output_files:
            print("\n✅ Export completed successfully!")
            for format_type, file_path in output_files.items():
                print(f"📄 {format_type.upper()}: {file_path}")
        else:
            print("❌ Export failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("Export interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()