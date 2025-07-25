#!/bin/bash

# Bench-based Insights Import Script
# Usage: ./bench_import.sh <import_directory_or_zip_file>

SITE="erp.tiqn.local"
IMPORT_PATH="$1"

# Check if import path is provided
if [ -z "$IMPORT_PATH" ]; then
    echo "❌ Usage: $0 <import_directory_or_zip_file>"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/insights_export_20250725_081227/"
    echo "  $0 /path/to/insights_export_20250725_081227.zip"
    exit 1
fi

# Check if import path exists
if [ ! -e "$IMPORT_PATH" ]; then
    echo "❌ Import path not found: $IMPORT_PATH"
    exit 1
fi

echo "🚀 Starting Insights import to $SITE"
echo "📁 Import from: $IMPORT_PATH"

# Check if we're in bench directory
if [ ! -f "sites/common_site_config.json" ]; then
    echo "❌ Must be run from frappe-bench directory"
    echo "Current directory: $(pwd)"
    echo "Please run: cd /home/sonnt/frappe-bench && $0 $IMPORT_PATH"
    exit 1
fi

# Check site exists
if [ ! -d "sites/$SITE" ]; then
    echo "❌ Site '$SITE' not found"
    echo "Available sites:"
    ls sites/ | grep -v -E "(assets|common_site_config.json|apps\.|insights_export)"
    exit 1
fi

echo "✅ Site found: $SITE"

# Handle ZIP file extraction
IMPORT_DIR="$IMPORT_PATH"
TEMP_EXTRACT_DIR=""

if [[ "$IMPORT_PATH" == *.zip ]]; then
    echo "📦 Extracting ZIP file..."
    TEMP_EXTRACT_DIR="/tmp/insights_import_$(date +%s)"
    mkdir -p "$TEMP_EXTRACT_DIR"
    
    unzip -q "$IMPORT_PATH" -d "$TEMP_EXTRACT_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to extract ZIP file"
        rm -rf "$TEMP_EXTRACT_DIR"
        exit 1
    fi
    
    IMPORT_DIR="$TEMP_EXTRACT_DIR"
    echo "✅ ZIP extracted to: $IMPORT_DIR"
fi

# Check if import directory contains JSON files
JSON_COUNT=$(find "$IMPORT_DIR" -name "*.json" -type f | wc -l)
if [ $JSON_COUNT -eq 0 ]; then
    echo "❌ No JSON files found in import directory"
    [ -n "$TEMP_EXTRACT_DIR" ] && rm -rf "$TEMP_EXTRACT_DIR"
    exit 1
fi

echo "📊 Found $JSON_COUNT JSON files to import"

# Create temp import script
TEMP_SCRIPT="/tmp/insights_import_$(date +%s).py"

cat > "$TEMP_SCRIPT" << EOF
import json
import os
from datetime import datetime

try:
    import_dir = '$IMPORT_DIR'
    print(f'🚀 Starting import to {frappe.local.site}')
    print(f'📁 Import from: {import_dir}')
    
    # Create backup before import
    print('💾 Creating backup before import...')
    try:
        from frappe.utils.backups import new_backup
        backup_path = new_backup(ignore_files=True)
        print(f'✅ Backup created: {backup_path}')
    except Exception as e:
        print(f'⚠️  Backup failed: {e}')
        print('Continuing without backup...')
    
    # DocType import order (dependencies first)
    import_order = [
        'insights_data_source.json',
        'insights_query_v3.json', 
        'insights_query.json',
        'insights_chart_v3.json',
        'insights_chart.json', 
        'insights_workbook.json',
        'insights_dashboard_v3.json',
        'insights_dashboard.json',
        'insights_dashboard_chart_v3.json',
        'insights_dashboard_chart.json'
    ]
    
    total_imported = 0
    import_summary = {
        "import_time": datetime.now().isoformat(),
        "site": frappe.local.site,
        "imported": {}
    }
    
    # Import files in order
    for filename in import_order:
        filepath = os.path.join(import_dir, filename)
        
        if not os.path.exists(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            if not records:
                print(f'📝 {filename}: No records')
                continue
                
            # Get DocType from first record
            doctype = records[0].get('doctype')
            if not doctype:
                print(f'❌ {filename}: No doctype field found')
                continue
                
            print(f'📊 {filename}: Importing {len(records)} {doctype} records')
            
            imported_count = 0
            for record_data in records:
                try:
                    record_name = record_data.get('name')
                    if not record_name:
                        continue
                    
                    # Check if record exists
                    if frappe.db.exists(doctype, record_name):
                        # Update existing
                        doc = frappe.get_doc(doctype, record_name)
                        for key, value in record_data.items():
                            if key not in ['name', 'doctype'] and hasattr(doc, key):
                                setattr(doc, key, value)
                        doc.save()
                        print(f'🔄 Updated: {record_name}')
                    else:
                        # Create new
                        doc = frappe.get_doc(record_data)
                        doc.insert()
                        print(f'➕ Created: {record_name}')
                    
                    frappe.db.commit()
                    imported_count += 1
                    
                except Exception as e:
                    print(f'❌ Error with {record_name}: {e}')
                    frappe.db.rollback()
            
            total_imported += imported_count
            import_summary["imported"][doctype] = {"count": imported_count, "file": filename}
            print(f'✅ {filename}: Imported {imported_count}/{len(records)} records')
            
        except Exception as e:
            print(f'❌ Error processing {filename}: {e}')
    
    print(f'\\n🎉 Import completed!')
    print(f'📊 Total records imported: {total_imported}')
    print(f'🔍 Please verify data in Insights app')
    print(f'IMPORT_SUCCESS:{total_imported}')
    
except Exception as e:
    print(f'💥 Import failed: {e}')
    import traceback
    traceback.print_exc()
EOF

echo "📝 Executing import via bench console..."

# Use bench console to run the import
bench --site "$SITE" console << CONSOLE_EOF
exec(open('$TEMP_SCRIPT').read())
CONSOLE_EOF

# Cleanup
rm -f "$TEMP_SCRIPT"
[ -n "$TEMP_EXTRACT_DIR" ] && rm -rf "$TEMP_EXTRACT_DIR"

echo ""
echo "✅ Import script completed. Check output above for results."
echo "🔍 Next steps:"
echo "   1. Login to ERPNext: http://$SITE"
echo "   2. Open Insights app"
echo "   3. Verify Dashboards, Charts, Queries"