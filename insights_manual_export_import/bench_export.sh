#!/bin/bash

# Bench-based Insights Export Script
# Must be run from frappe-bench directory

SITE="${1:-erp-sonnt.tiqn.local}"
SCRIPT_DIR="/home/sonnt/frappe-bench/sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/insights_manual_export_import"

echo "🚀 Starting Insights export from $SITE"

# Check if we're in bench directory
if [ ! -f "sites/common_site_config.json" ]; then
    echo "❌ Must be run from frappe-bench directory"
    echo "Current directory: $(pwd)"
    echo "Please run: cd /home/sonnt/frappe-bench && $0 $SITE"
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

# Create temp export script
TEMP_SCRIPT="/tmp/insights_export_$(date +%s).py"

cat > "$TEMP_SCRIPT" << 'EOF'
import json
import os
from datetime import datetime

try:
    # Create export directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    script_dir = '/home/sonnt/frappe-bench/sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/insights_manual_export_import'
    export_dir = os.path.join(script_dir, f'insights_export_{timestamp}')
    os.makedirs(export_dir, exist_ok=True)

    print(f'🚀 Starting export from {frappe.local.site}')
    print(f'📁 Export directory: {export_dir}')

    # DocTypes to check
    doctypes_to_check = [
        'Insights Data Source',
        'Insights Workbook', 
        'Insights Query v3',
        'Insights Query',
        'Insights Chart v3', 
        'Insights Chart',
        'Insights Dashboard v3',
        'Insights Dashboard',
        'Insights Dashboard Chart v3',
        'Insights Dashboard Chart'
    ]

    total_exported = 0
    summary = {
        "export_time": datetime.now().isoformat(),
        "site": frappe.local.site,
        "exported": {}
    }

    for doctype in doctypes_to_check:
        try:
            if not frappe.db.exists('DocType', doctype):
                continue
                
            count = frappe.db.count(doctype)
            if count == 0:
                print(f'📝 {doctype}: 0 records')
                continue
                
            print(f'📊 {doctype}: {count} records')
            
            # Get all records
            records = frappe.get_all(doctype, fields=['name'])
            exported_records = []
            
            for record in records:
                try:
                    doc = frappe.get_doc(doctype, record.name)
                    doc_data = doc.as_dict()
                    
                    # Clean system fields
                    for field in ['creation', 'modified', 'modified_by', 'owner', 'idx']:
                        doc_data.pop(field, None)
                    
                    exported_records.append(doc_data)
                except Exception as e:
                    print(f'⚠️  Failed to export {record.name}: {e}')
            
            if exported_records:
                # Save to JSON
                filename = f'{doctype.replace(" ", "_").lower()}.json'
                filepath = os.path.join(export_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(exported_records, f, indent=2, default=str, ensure_ascii=False)
                
                total_exported += len(exported_records)
                summary["exported"][doctype] = {"count": len(exported_records), "file": filename}
                print(f'✅ {doctype}: exported {len(exported_records)} records → {filename}')
        
        except Exception as e:
            print(f'❌ Error with {doctype}: {e}')

    # Save summary
    with open(os.path.join(export_dir, 'export_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str, ensure_ascii=False)

    print(f'\n🎉 Export completed!')
    print(f'📁 Location: {export_dir}')
    print(f'📊 Total records: {total_exported}')
    print(f'EXPORT_SUCCESS:{export_dir}')

except Exception as e:
    print(f'💥 Export failed: {e}')
    import traceback
    traceback.print_exc()
EOF

echo "📝 Executing export via bench console..."

# Use bench console to run the script
bench --site "$SITE" console << CONSOLE_EOF
exec(open('$TEMP_SCRIPT').read())
CONSOLE_EOF

# Cleanup
rm -f "$TEMP_SCRIPT"

echo ""
echo "✅ Export script completed. Check output above for results."