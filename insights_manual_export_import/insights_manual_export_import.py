#!/usr/bin/env python3
"""
Insights Manual Export/Import Script
Simple export to files and manual import for Insights data transfer
"""

import frappe
import json
import os
import csv
import zipfile
import sys
from datetime import datetime

class InsightsManualTransfer:
    def __init__(self, site, mode="export"):
        self.site = site
        self.mode = mode
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get script directory (where the script is located)
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.export_dir = os.path.join(self.script_dir, f"insights_export_{self.timestamp}")
        
        # Insights DocTypes in dependency order
        self.doctypes = [
            "Insights Settings",
            "Insights Data Source", 
            "Insights Query",
            "Insights Chart", 
            "Insights Workbook",
            "Insights Dashboard"
        ]
        
        # Alternative DocType names (some versions might use different names)
        self.doctype_alternatives = {
            "Insights Dashboard": ["Dashboard", "Insights Dashboard"],
            "Insights Chart": ["Chart", "Insights Chart"],
            "Insights Query": ["Query", "Insights Query"], 
            "Insights Data Source": ["Query Data Source", "Insights Data Source"],
            "Insights Workbook": ["Insights Workbook"],
            "Insights Settings": ["Insights Settings"]
        }
        
        # Create export directory
        if mode == "export":
            os.makedirs(self.export_dir, exist_ok=True)
            
    def log(self, message, level="INFO"):
        """Simple logging"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")

    def get_actual_doctype_name(self, doctype):
        """Get the actual DocType name that exists in the system"""
        alternatives = self.doctype_alternatives.get(doctype, [doctype])
        
        for alt_name in alternatives:
            if frappe.db.exists("DocType", alt_name):
                return alt_name
        
        return None

    def export_to_json(self):
        """Export all Insights data to JSON files"""
        self.log(f"Starting JSON export from {self.site}")
        
        frappe.init(site=self.site)
        frappe.connect()
        
        export_summary = {
            "export_time": datetime.now().isoformat(),
            "site": self.site,
            "exported_doctypes": {},
            "total_records": 0
        }
        
        try:
            for doctype in self.doctypes:
                actual_doctype = self.get_actual_doctype_name(doctype)
                
                if not actual_doctype:
                    self.log(f"DocType not found: {doctype}", "WARNING")
                    continue
                
                try:
                    # Count records
                    count = frappe.db.count(actual_doctype)
                    if count == 0:
                        self.log(f"No data in {actual_doctype}")
                        continue
                    
                    self.log(f"Exporting {count} records from {actual_doctype}")
                    
                    # Get all records
                    records = frappe.get_all(actual_doctype)
                    
                    # Get full document data
                    full_records = []
                    for record in records:
                        try:
                            doc = frappe.get_doc(actual_doctype, record.name)
                            doc_dict = doc.as_dict()
                            
                            # Remove system fields
                            system_fields = ['creation', 'modified', 'modified_by', 'owner', 'idx']
                            for field in system_fields:
                                if field in doc_dict:
                                    del doc_dict[field]
                            
                            full_records.append(doc_dict)
                            
                        except Exception as e:
                            self.log(f"Error exporting {record.name}: {str(e)}", "ERROR")
                    
                    # Save to JSON file
                    filename = f"{actual_doctype.replace(' ', '_').lower()}.json"
                    filepath = os.path.join(self.export_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(full_records, f, indent=2, default=str, ensure_ascii=False)
                    
                    export_summary["exported_doctypes"][actual_doctype] = {
                        "count": len(full_records),
                        "file": filename
                    }
                    export_summary["total_records"] += len(full_records)
                    
                    self.log(f"✅ Exported {len(full_records)} records to {filename}")
                    
                except Exception as e:
                    self.log(f"Error exporting {actual_doctype}: {str(e)}", "ERROR")
            
            # Save export summary
            with open(os.path.join(self.export_dir, "export_summary.json"), 'w', encoding='utf-8') as f:
                json.dump(export_summary, f, indent=2, default=str, ensure_ascii=False)
            
            self.log(f"✅ JSON export completed: {self.export_dir}")
            return True, self.export_dir
            
        except Exception as e:
            self.log(f"Export failed: {str(e)}", "ERROR")
            return False, None
        finally:
            frappe.destroy()

    def export_to_sql(self):
        """Export Insights data to SQL files"""
        self.log(f"Starting SQL export from {self.site}")
        
        frappe.init(site=self.site)
        frappe.connect()
        
        try:
            sql_file = os.path.join(self.export_dir, "insights_data.sql")
            
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write("-- Insights Data Export\n")
                f.write(f"-- Generated: {datetime.now()}\n")
                f.write(f"-- Source Site: {self.site}\n\n")
                
                for doctype in self.doctypes:
                    actual_doctype = self.get_actual_doctype_name(doctype)
                    
                    if not actual_doctype:
                        continue
                    
                    count = frappe.db.count(actual_doctype)
                    if count == 0:
                        continue
                    
                    self.log(f"Exporting {count} records from {actual_doctype} to SQL")
                    
                    # Get table name
                    table_name = f"tab{actual_doctype}"
                    
                    f.write(f"\n-- {actual_doctype} ({count} records)\n")
                    
                    # Get all records
                    records = frappe.db.sql(f"SELECT * FROM `{table_name}`", as_dict=True)
                    
                    if records:
                        # Get column names
                        columns = list(records[0].keys())
                        
                        f.write(f"DELETE FROM `{table_name}`;\n")
                        
                        for record in records:
                            values = []
                            for col in columns:
                                value = record[col]
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, str):
                                    # Escape single quotes
                                    escaped_value = value.replace("'", "\\'")
                                    values.append(f"'{escaped_value}'")
                                else:
                                    values.append(f"'{value}'")
                            
                            columns_str = "`, `".join(columns)
                            values_str = ", ".join(values)
                            
                            f.write(f"INSERT INTO `{table_name}` (`{columns_str}`) VALUES ({values_str});\n")
                    
                    f.write("\n")
            
            self.log(f"✅ SQL export completed: {sql_file}")
            return True, sql_file
            
        except Exception as e:
            self.log(f"SQL export failed: {str(e)}", "ERROR")
            return False, None
        finally:
            frappe.destroy()

    def export_to_csv(self):
        """Export Insights data to CSV files"""
        self.log(f"Starting CSV export from {self.site}")
        
        frappe.init(site=self.site)
        frappe.connect()
        
        try:
            csv_dir = os.path.join(self.export_dir, "csv")
            os.makedirs(csv_dir, exist_ok=True)
            
            for doctype in self.doctypes:
                actual_doctype = self.get_actual_doctype_name(doctype)
                
                if not actual_doctype:
                    continue
                
                count = frappe.db.count(actual_doctype)
                if count == 0:
                    continue
                
                self.log(f"Exporting {count} records from {actual_doctype} to CSV")
                
                # Get records
                records = frappe.get_all(actual_doctype)
                
                if not records:
                    continue
                
                # Get full record data
                full_records = []
                for record in records:
                    try:
                        doc = frappe.get_doc(actual_doctype, record.name)
                        doc_dict = doc.as_dict()
                        
                        # Remove system fields
                        system_fields = ['creation', 'modified', 'modified_by', 'owner', 'idx']
                        for field in system_fields:
                            if field in doc_dict:
                                del doc_dict[field]
                        
                        # Convert complex fields to JSON strings
                        for key, value in doc_dict.items():
                            if isinstance(value, (dict, list)):
                                doc_dict[key] = json.dumps(value, default=str)
                        
                        full_records.append(doc_dict)
                        
                    except Exception as e:
                        self.log(f"Error processing {record.name}: {str(e)}", "ERROR")
                
                if full_records:
                    # Save to CSV
                    filename = f"{actual_doctype.replace(' ', '_').lower()}.csv"
                    filepath = os.path.join(csv_dir, filename)
                    
                    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                        fieldnames = full_records[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        writer.writeheader()
                        writer.writerows(full_records)
                    
                    self.log(f"✅ Exported {len(full_records)} records to {filename}")
            
            return True, csv_dir
            
        except Exception as e:
            self.log(f"CSV export failed: {str(e)}", "ERROR")
            return False, None
        finally:
            frappe.destroy()

    def create_export_package(self):
        """Create a ZIP package with all export formats"""
        self.log("Creating export package...")
        
        # Export to all formats
        json_success, json_path = self.export_to_json()
        sql_success, sql_path = self.export_to_sql()
        csv_success, csv_path = self.export_to_csv()
        
        if not json_success:
            return False, None
        
        # Create ZIP file in script directory
        zip_filename = f"insights_export_{self.timestamp}.zip"
        zip_path = os.path.join(self.script_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON files
            for root, dirs, files in os.walk(self.export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.export_dir)
                    zipf.write(file_path, arcname)
        
        # Clean up temporary export directory
        import shutil
        shutil.rmtree(self.export_dir)
        
        self.log(f"✅ Export package created: {zip_path}")
        return True, zip_path

    def import_from_json(self, import_dir):
        """Import data from JSON files"""
        self.log(f"Starting JSON import to {self.site}")
        
        frappe.init(site=self.site)  
        frappe.connect()
        
        try:
            # Create backup first
            self.log("Creating backup before import...")
            os.system(f"bench --site {self.site} backup")
            
            imported_total = 0
            
            # Import in dependency order
            for doctype in self.doctypes:
                json_filename = f"{doctype.replace(' ', '_').lower()}.json"
                json_path = os.path.join(import_dir, json_filename)
                
                if not os.path.exists(json_path):
                    self.log(f"File not found: {json_filename}", "WARNING")
                    continue
                
                # Get actual doctype name
                actual_doctype = self.get_actual_doctype_name(doctype)
                if not actual_doctype:
                    self.log(f"DocType not found in system: {doctype}", "ERROR")
                    continue
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                    
                    self.log(f"Importing {len(records)} records to {actual_doctype}")
                    
                    imported_count = 0
                    for record_data in records:
                        try:
                            record_name = record_data.get('name')
                            
                            # Check if record exists
                            if frappe.db.exists(actual_doctype, record_name):
                                # Update existing
                                doc = frappe.get_doc(actual_doctype, record_name)
                                for key, value in record_data.items():
                                    if key != 'name' and hasattr(doc, key):
                                        setattr(doc, key, value)
                                doc.save()
                                self.log(f"Updated: {record_name}")
                            else:
                                # Create new
                                doc = frappe.get_doc(record_data)
                                doc.insert()
                                self.log(f"Created: {record_name}")
                            
                            frappe.db.commit()
                            imported_count += 1
                            
                        except Exception as e:
                            self.log(f"Error importing {record_data.get('name', 'Unknown')}: {str(e)}", "ERROR")
                            frappe.db.rollback()
                    
                    self.log(f"✅ Imported {imported_count}/{len(records)} records from {json_filename}")
                    imported_total += imported_count
                    
                except Exception as e:
                    self.log(f"Error processing {json_filename}: {str(e)}", "ERROR")
            
            self.log(f"✅ Import completed. Total records imported: {imported_total}")
            return True
            
        except Exception as e:
            self.log(f"Import failed: {str(e)}", "ERROR")
            return False
        finally:
            frappe.destroy()

    def import_from_zip(self, zip_path):
        """Import from ZIP package"""
        self.log(f"Importing from ZIP: {zip_path}")
        
        if not os.path.exists(zip_path):
            self.log(f"ZIP file not found: {zip_path}", "ERROR")
            return False
        
        # Extract ZIP to script directory
        extract_dir = os.path.join(self.script_dir, f"insights_import_{self.timestamp}")
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        # Import from extracted files
        success = self.import_from_json(extract_dir)
        
        # Cleanup
        import shutil
        shutil.rmtree(extract_dir)
        
        return success


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Export: python3 script.py export <site_name> [format]")
        print("  Import: python3 script.py import <site_name> <file_or_dir_path>")
        print("")
        print("Export formats: json, sql, csv, all (default: all)")
        print("")
        print("Examples:")
        print("  python3 script.py export erp-sonnt.tiqn.local")
        print("  python3 script.py export erp-sonnt.tiqn.local json")
        print("  python3 script.py import erp.tiqn.local /path/to/insights_export.zip")
        print("  python3 script.py import erp.tiqn.local /path/to/json/folder")
        return
    
    mode = sys.argv[1]
    site = sys.argv[2]
    
    if mode == "export":
        export_format = sys.argv[3] if len(sys.argv) > 3 else "all"
        
        transfer = InsightsManualTransfer(site, mode="export")
        
        print(f"🚀 Starting export from {site}")
        print(f"📋 Format: {export_format}")
        
        if export_format == "json":
            success, path = transfer.export_to_json()
        elif export_format == "sql":
            success, path = transfer.export_to_sql()
        elif export_format == "csv":
            success, path = transfer.export_to_csv()
        else:  # all
            success, path = transfer.create_export_package()
        
        if success:
            print(f"✅ Export completed successfully!")
            print(f"📁 Export location: {path}")
            print(f"📋 Next steps:")
            print(f"   1. Copy {path} to target server")
            print(f"   2. Run: python3 script.py import {site} {path}")
        else:
            print("❌ Export failed!")
    
    elif mode == "import":
        if len(sys.argv) < 4:
            print("❌ Import path required")
            print("Usage: python3 script.py import <site_name> <file_or_dir_path>")
            return
        
        import_path = sys.argv[3]
        
        transfer = InsightsManualTransfer(site, mode="import")
        
        print(f"🚀 Starting import to {site}")
        print(f"📁 Import from: {import_path}")
        
        if import_path.endswith('.zip'):
            success = transfer.import_from_zip(import_path)
        else:
            success = transfer.import_from_json(import_path)
        
        if success:
            print("✅ Import completed successfully!")
            print("🔔 Please verify your data in Insights app")
        else:
            print("❌ Import failed!")
    
    else:
        print("❌ Invalid mode. Use 'export' or 'import'")


if __name__ == "__main__":
    main()