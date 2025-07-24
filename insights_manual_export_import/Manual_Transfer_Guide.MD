# Hướng Dẫn Export/Import Thủ Công Insights Data

## 📋 Tổng Quan

Script `insights_manual_export_import.py` được thiết kế để export Insights data thành các file có thể transfer thủ công giữa các servers khác nhau.

### ✨ Tính Năng:
- 🗃️ **Export đa định dạng**: JSON, SQL, CSV
- 📦 **Tạo ZIP package** chứa tất cả formats
- 🔄 **Import tự động** từ JSON hoặc ZIP
- 🛡️ **Backup tự động** trước khi import
- 📊 **Báo cáo chi tiết** quá trình export/import

### 📁 Các Data Được Transfer:
- ✅ **Dashboards** - Bảng điều khiển
- ✅ **Workbooks** - Sổ làm việc  
- ✅ **Data Sources** - Nguồn dữ liệu
- ✅ **Charts** - Biểu đồ
- ✅ **Queries** - Truy vấn
- ✅ **Settings** - Cài đặt

## 🛠️ Yêu Cầu Hệ Thống

### Trên Cả 2 Servers:
- **ERPNext/Frappe Framework** đã cài đặt
- **Insights App** đã cài đặt
- **Python 3.x**
- **Quyền truy cập** bench commands

### Kiểm Tra Insights App:
```bash
# Kiểm tra app
bench --site your-site list-apps | grep insights

# Cài đặt nếu chưa có
bench get-app insights
bench --site your-site install-app insights
```

## 📥 Cài Đặt Script

### 1. Tải Script
```bash
# Tạo thư mục
mkdir -p ~/insights-transfer
cd ~/insights-transfer

# Tạo script file
nano insights_manual_export_import.py
# (Copy nội dung từ artifact)

# Phân quyền
chmod +x insights_manual_export_import.py
```

### 2. Test Script
```bash
# Test script
python3 insights_manual_export_import.py
```

## 🚀 Cách Sử Dụng

### 📤 EXPORT DATA (Trên Server Nguồn)

#### 1. Export Sử Dụng Bench Console (Khuyến nghị)
```bash
cd ~/frappe-bench
bench --site erp-sonnt.tiqn.local console
```

Sau đó paste đoạn code sau vào console:
```python
import json
import os
from datetime import datetime

# Simple export function
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
export_dir = f'insights_export_{timestamp}'
os.makedirs(export_dir, exist_ok=True)

doctypes = ['Insights Settings', 'Insights Data Source', 'Insights Query', 'Insights Chart', 'Insights Workbook', 'Insights Dashboard']

print(f'Starting export from {frappe.local.site}')
total_records = 0

for doctype in doctypes:
    try:
        if not frappe.db.exists('DocType', doctype):
            print(f'DocType {doctype} not found, skipping')
            continue
        
        records = frappe.get_all(doctype, fields=['name'])
        print(f'Found {len(records)} {doctype} records')
        
        if not records:
            continue
        
        full_records = []
        for record in records:
            try:
                doc = frappe.get_doc(doctype, record.name)
                doc_dict = doc.as_dict()
                
                system_fields = ['creation', 'modified', 'modified_by', 'owner', 'idx']
                for field in system_fields:
                    if field in doc_dict:
                        del doc_dict[field]
                
                full_records.append(doc_dict)
            except Exception as e:
                print(f'Error exporting {record.name}: {str(e)}')
        
        filename = f'{doctype.replace(" ", "_").lower()}.json'
        filepath = os.path.join(export_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_records, f, indent=2, default=str, ensure_ascii=False)
        
        total_records += len(full_records)
        print(f'Exported {len(full_records)} {doctype} records to {filename}')
        
    except Exception as e:
        print(f'Error processing {doctype}: {str(e)}')

print(f'Export completed! Files saved to: {export_dir}')
print(f'Total records exported: {total_records}')
```

**Output mẫu:**
```
Starting export from erp-sonnt.tiqn.local
Found 2 Insights Data Source records
Exported 2 Insights Data Source records to insights_data_source.json
Found 1 Insights Workbook records  
Exported 1 Insights Workbook records to insights_workbook.json
Export completed! Files saved to: insights_export_20250724_203809
Total records exported: 3
```

#### 2. Export Sử Dụng Script (Thay thế)
**⚠️ Lưu ý: Script cần chạy từ thư mục bench và có thể cần sửa đường dẫn**

```bash
cd ~/frappe-bench
env/bin/python sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/insights_manual_export_import/insights_manual_export_import.py export erp-sonnt.tiqn.local
```

### 📂 Cấu Trúc File Export

**Console Export (Thư mục JSON):**
```
~/frappe-bench/sites/insights_export_20250724_203809/
├── insights_data_source.json        # Data source data (2 records)
├── insights_workbook.json           # Workbook data (1 record)
└── (các file khác nếu có data)
```

**Script Export (ZIP Package - nếu script hoạt động):**
```
insights_export_20240724_103015.zip
├── export_summary.json              # Tóm tắt export
├── insights_dashboard.json          # Dashboard data
├── insights_chart.json              # Chart data  
├── insights_query.json              # Query data
├── insights_data_source.json        # Data source data
├── insights_workbook.json           # Workbook data
├── insights_settings.json           # Settings data
├── insights_data.sql                # SQL dump
└── csv/                             # CSV files
    ├── insights_dashboard.csv
    ├── insights_chart.csv
    └── ...
```

**Ví dụ thực tế từ export gần đây:**
```
sites/insights_export_20250724_203809/
├── insights_data_source.json        # 2 data sources: Site DB, Query Store
└── insights_workbook.json           # 1 workbook: "Inline" với 2 queries và 2 charts
```

## 📋 Transfer Files Giữa Servers

### Phương Pháp 1: SCP (Khuyến nghị)
```bash
# Copy thư mục export từ console
scp -r ~/frappe-bench/sites/insights_export_20250724_203809/ user@target-server:~/insights-transfer/

# Copy ZIP file (nếu có từ script)
scp ~/insights-transfer/insights_export_20240724_103015.zip user@target-server:~/insights-transfer/
```

### Phương Pháp 2: SFTP
```bash
sftp user@target-server
# Upload thư mục export
put -r ~/frappe-bench/sites/insights_export_20250724_203809/ ~/insights-transfer/
quit
```

### Phương Pháp 3: ZIP và Transfer
```bash
# Tạo ZIP từ export directory
cd ~/frappe-bench/sites/
zip -r insights_export_20250724_203809.zip insights_export_20250724_203809/

# Transfer ZIP
scp insights_export_20250724_203809.zip user@target-server:~/insights-transfer/

# Trên server đích: extract
cd ~/insights-transfer/
unzip insights_export_20250724_203809.zip
```

### Phương Pháp 4: Cloud Storage
```bash
# Upload lên Google Drive/Dropbox/AWS S3
zip -r insights_export.zip ~/frappe-bench/sites/insights_export_*/
# Upload bằng web interface hoặc CLI tools
# Download trên server đích vào ~/insights-transfer/
```

## 📥 IMPORT DATA (Trên Server Đích)

### 1. Import Sử Dụng Bench Console (Khuyến nghị)
```bash
cd ~/frappe-bench
bench --site erp.tiqn.local console
```

Sau đó paste đoạn code sau vào console:
```python
import json
import os
from datetime import datetime

def import_insights_data(import_dir):
    """Import insights data from exported JSON files"""
    
    print(f'🚀 Starting import to {frappe.local.site}')
    print(f'📁 Import from: {import_dir}')
    
    # Tạo backup trước khi import
    print('[INFO] Creating backup before import...')
    frappe.utils.backup.new_backup(ignore_files=True, backup_path_db='/tmp/')
    
    # Thứ tự import theo dependency
    import_order = [
        "insights_settings.json",
        "insights_data_source.json", 
        "insights_query.json",
        "insights_chart.json",
        "insights_workbook.json",
        "insights_dashboard.json"
    ]
    
    total_imported = 0
    
    for filename in import_order:
        filepath = os.path.join(import_dir, filename)
        
        if not os.path.exists(filepath):
            print(f'File {filename} not found, skipping')
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                records = json.load(f)
                
            if not records:
                print(f'No records in {filename}')
                continue
                
            doctype = records[0].get('doctype')
            print(f'[INFO] Importing {len(records)} records to {doctype}')
            
            imported_count = 0
            for record in records:
                try:
                    # Xóa các field không cần thiết
                    if 'doctype' in record:
                        del record['doctype']
                    
                    # Kiểm tra record đã tồn tại chưa
                    existing = None
                    try:
                        existing = frappe.get_doc(doctype, record['name'])
                        print(f'[INFO] Updated: {record.get("title", record["name"])}')
                        # Update existing record
                        for key, value in record.items():
                            setattr(existing, key, value)
                        existing.save()
                    except frappe.DoesNotExistError:
                        # Tạo record mới
                        new_doc = frappe.get_doc(record)
                        new_doc.doctype = doctype
                        new_doc.insert()
                        print(f'[INFO] Created: {record.get("title", record["name"])}')
                    
                    imported_count += 1
                    
                except Exception as e:
                    print(f'[ERROR] Failed to import {record.get("name", "unknown")}: {str(e)}')
            
            total_imported += imported_count
            print(f'✅ Imported {imported_count}/{len(records)} records from {filename}')
            
        except Exception as e:
            print(f'[ERROR] Failed to process {filename}: {str(e)}')
    
    print(f'✅ Import completed! Total records: {total_imported}')
    print('🔔 Please verify your data in Insights app')
    
    return total_imported

# Sử dụng function với đường dẫn export directory
import_dir = '/home/frappe/frappe-bench/insights-transfer/insights_export_20250724_203809'  # Sửa đường dẫn
import_insights_data(import_dir)
```

### 2. Import Sử Dụng Script (Thay thế)
```bash
cd ~/frappe-bench
env/bin/python sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/insights_manual_export_import/insights_manual_export_import.py import erp.tiqn.local ~/insights-transfer/insights_export_20250724_203809/
```

**Output Import mẫu:**
```
🚀 Starting import to erp.tiqn.local
📁 Import from: /home/frappe/frappe-bench/insights-transfer/insights_export_20250724_203809
[INFO] Creating backup before import...
[INFO] Importing 2 records to Insights Data Source
[INFO] Created: Site DB
[INFO] Created: Query Store  
✅ Imported 2/2 records from insights_data_source.json
[INFO] Importing 1 records to Insights Workbook
[INFO] Created: Inline
✅ Imported 1/1 records from insights_workbook.json
✅ Import completed! Total records: 3
🔔 Please verify your data in Insights app
```

## 🔧 Scripts Tự Động Hóa

### Export Script (`export_insights.sh`)
```bash
#!/bin/bash

SITE="erp-sonnt.tiqn.local"
SCRIPT_DIR="~/insights-transfer"
SCRIPT_PATH="$SCRIPT_DIR/insights_manual_export_import.py"

echo "🚀 Starting Insights export..."

# Export
cd ~/frappe-bench
python3 $SCRIPT_PATH export $SITE

# Tìm file export mới nhất trong script directory
EXPORT_FILE=$(ls -t $SCRIPT_DIR/insights_export_*.zip 2>/dev/null | head -1)

if [ -f "$EXPORT_FILE" ]; then
    echo "✅ Export completed: $EXPORT_FILE"
    echo "📋 File size: $(du -h $EXPORT_FILE | cut -f1)"
    echo ""
    echo "📤 Transfer commands:"
    echo "   scp $EXPORT_FILE user@target-server:~/insights-transfer/"
    echo "   rsync -avz $EXPORT_FILE user@target-server:~/insights-transfer/"
else
    echo "❌ No export file found!"
fi
```

### Import Script (`import_insights.sh`)
```bash
#!/bin/bash

SITE="erp.tiqn.local"
SCRIPT_DIR="~/insights-transfer"
SCRIPT_PATH="$SCRIPT_DIR/insights_manual_export_import.py"

echo "🚀 Starting Insights import..."

# Tìm file import mới nhất trong script directory
IMPORT_FILE=$(ls -t $SCRIPT_DIR/insights_export_*.zip 2>/dev/null | head -1)

if [ -f "$IMPORT_FILE" ]; then
    echo "📦 Import file: $IMPORT_FILE"
    echo "📋 File size: $(du -h $IMPORT_FILE | cut -f1)"
    
    # Import
    cd ~/frappe-bench
    python3 $SCRIPT_PATH import $SITE $IMPORT_FILE
    
    if [ $? -eq 0 ]; then
        echo "✅ Import completed successfully!"
        echo "🔔 Please check Insights app to verify data"
    else
        echo "❌ Import failed!"
    fi
else
    echo "❌ No import file found in $SCRIPT_DIR"
    echo "Available files:"
    ls -la $SCRIPT_DIR/insights_export_* 2>/dev/null || echo "   (none)"
fi
```

### Chạy Scripts:
```bash
# Trên server nguồn
chmod +x export_insights.sh
./export_insights.sh

# Trên server đích
chmod +x import_insights.sh  
./import_insights.sh
```

## 🔍 Troubleshooting

### Lỗi Export

#### 1. "Site not found"
```bash
# Kiểm tra sites
bench --site all list-sites

# Hoặc
ls sites/
```

#### 2. "DocType not found"
```bash
# Kiểm tra Insights app
bench --site erp-sonnt.tiqn.local list-apps | grep insights

# Cài đặt nếu thiếu
bench --site erp-sonnt.tiqn.local install-app insights
```

#### 3. "Permission denied"
```bash
# Kiểm tra quyền trong script directory
ls -la ~/insights-transfer/

# Tạo thư mục nếu cần
mkdir -p ~/insights-transfer
chmod 755 ~/insights-transfer
```

### Lỗi Transfer

#### 1. "No space left on device"
```bash
# Kiểm tra dung lượng
df -h

# Dọn dẹp files cũ trong script directory
rm -f ~/insights-transfer/insights_export_*.zip
rm -rf ~/insights-transfer/insights_export_*/
```

#### 2. "Connection refused" (SCP)
```bash
# Kiểm tra SSH service trên target
ssh user@target-server "sudo systemctl status ssh"

# Test connection
telnet target-server 22
```

#### 3. "File too large"
```bash
# Nén file tốt hơn
cd /tmp
zip -9 insights_export_compressed.zip insights_export_*.zip

# Hoặc chia nhỏ file
split -b 100M insights_export_large.zip insights_part_
```

### Lỗi Import

#### 1. "Import file not found"
```bash
# Kiểm tra file trong script directory
ls -la ~/insights-transfer/insights_export_*

# Kiểm tra nội dung ZIP
unzip -l ~/insights-transfer/insights_export_*.zip
```

#### 2. "Backup failed"
```bash
# Tạo backup manual
bench --site erp.tiqn.local backup

# Hoặc skip backup (không khuyến nghị)
# Sửa trong script: comment dòng backup
```

#### 3. "DocType not found in system"
```bash
# Cài đặt Insights app
bench --site erp.tiqn.local install-app insights

# Migrate
bench --site erp.tiqn.local migrate

# Restart
bench restart
```

## 📊 Kiểm Tra Kết Quả

### 1. Xem Export Summary
```bash
# Giải nén và xem summary
unzip -p ~/insights-transfer/insights_export_*.zip export_summary.json | python3 -m json.tool
```

### 2. Verify Import Data
```bash
# Vào Frappe console
bench --site erp.tiqn.local console
```

```python
# Kiểm tra số lượng records
doctypes = [
    "Insights Dashboard",
    "Insights Chart", 
    "Insights Query",
    "Insights Data Source",
    "Insights Workbook"
]

for dt in doctypes:
    try:
        count = frappe.db.count(dt)
        print(f"{dt}: {count} records")
    except:
        print(f"{dt}: DocType not found")

# Kiểm tra dashboard cụ thể
dashboards = frappe.get_all("Insights Dashboard", fields=["name", "title"])
for d in dashboards:
    print(f"Dashboard: {d.name} - {d.title}")
```

### 3. Test Trong Insights App
1. **Login** vào ERPNext site đích
2. **Mở Insights app**
3. **Kiểm tra Dashboards** hiển thị
4. **Test Charts** render đúng
5. **Verify Data Sources** connect được

## ⚠️ Lưu Ý Quan Trọng

### Trước Khi Export:
- ✅ **Backup site nguồn** để đảm bảo an toàn
- ✅ **Kiểm tra dung lượng disk** trên cả 2 servers
- ✅ **Note lại các custom settings** có thể bị mất
- ✅ **Chạy từ thư mục bench** (`~/frappe-bench`)

### Trước Khi Import:
- ✅ **Backup site đích** (import script tự động làm)
- ✅ **Đảm bảo Insights app** đã cài đặt và active
- ✅ **Kiểm tra version compatibility** giữa 2 sites  
- ✅ **Sửa đường dẫn** trong import script cho đúng

### Sau Khi Import: 
- ✅ **Test toàn bộ dashboards** hoạt động
- ✅ **Kiểm tra data sources** còn valid
- ✅ **Verify user permissions** trên items mới
- ✅ **Update queries** nếu cần thiết
- ✅ **Test charts render** đúng dữ liệu

### Kết Quả Thực Tế (24/07/2025):
- ✅ **Export thành công**: 3 records (2 Data Sources + 1 Workbook)
- ✅ **Data Sources**: Site DB (MariaDB), Query Store (SQLite)  
- ✅ **Workbook**: "Inline" với 2 queries QC và 2 charts tiếng Việt
- ✅ **Files tạo**: insights_data_source.json, insights_workbook.json

## 🎯 Best Practices

### 1. Naming Convention
```bash
# Đặt tên file có ý nghĩa
insights_export_$(date +%Y%m%d)_$(hostname)_to_production.zip
```

### 2. Documentation
```bash
# Tạo file ghi chú
cat > transfer_notes.txt << EOF
Transfer Date: $(date)
Source: erp-sonnt.tiqn.local  
Target: erp.tiqn.local
Exported Items:
- 5 Dashboards
- 12 Charts  
- 8 Queries
- 3 Data Sources
Notes: Transferred for production deployment
EOF
```

### 3. Version Control
```bash
# Git track export files (nếu cần)
git add insights_export_*.zip
git commit -m "Export insights data for production transfer"
```

### 4. Automation
```bash
# Cron job để export định kỳ
0 2 * * 0 cd /home/frappe/frappe-bench && python3 ~/insights-transfer/insights_manual_export_import.py export erp-sonnt.tiqn.local >/tmp/export.log 2>&1
```

## 📞 Hỗ Trợ

### Log Files
```bash
# Check export logs
tail -f /tmp/insights_export_*/export.log

# Check import logs  
tail -f /tmp/insights_import.log
```

### Debug Mode
Thêm debug vào script:
```python
def log(self, message, level="INFO"):
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_msg = f"[{timestamp}] {level}: {message}"
    print(log_msg)
    
    # Debug file
    with open("/tmp/insights_debug.log", "a") as f:
        f.write(log_msg + "\n")
```

---

**💡 Pro Tips:**
- Luôn test trên dev environment trước
- Sử dụng rsync với `--progress` để track transfer lớn
- Compress ZIP với level 9 để tiết kiệm băng thông: `zip -9`
- Backup không chỉ data mà cả customizations