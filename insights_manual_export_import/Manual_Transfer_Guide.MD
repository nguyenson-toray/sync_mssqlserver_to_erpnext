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

#### 1. Export Tất Cả Formats (Khuyến nghị)
```bash
cd ~/frappe-bench
python3 ~/insights-transfer/insights_manual_export_import.py export erp-sonnt.tiqn.local
```

**Output:**
```
✅ Export completed successfully!
📁 Export location: ~/insights-transfer/insights_export_20240724_103015.zip
📋 Next steps:
   1. Copy ~/insights-transfer/insights_export_20240724_103015.zip to target server
   2. Run: python3 script.py import erp.tiqn.local ~/insights-transfer/insights_export_20240724_103015.zip
```

#### 2. Export Chỉ JSON
```bash
python3 insights_manual_export_import.py export erp-sonnt.tiqn.local json
```

#### 3. Export Chỉ SQL
```bash
python3 insights_manual_export_import.py export erp-sonnt.tiqn.local sql
```

#### 4. Export Chỉ CSV
```bash
python3 insights_manual_export_import.py export erp-sonnt.tiqn.local csv
```

### 📂 Cấu Trúc File Export

**ZIP Package (all format):**
```
insights_export_20240724_103015.zip (trong thư mục script)
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

**JSON Only:**
```
~/insights-transfer/
├── insights_export_20240724_103015/
│   ├── export_summary.json
│   ├── insights_dashboard.json
│   ├── insights_chart.json
│   └── ...
└── insights_manual_export_import.py
```

## 📋 Transfer Files Giữa Servers

### Phương Pháp 1: SCP (Khuyến nghị)
```bash
# Copy ZIP file
scp ~/insights-transfer/insights_export_20240724_103015.zip user@target-server:~/insights-transfer/

# Copy thư mục JSON (nếu export JSON only)
scp -r ~/insights-transfer/insights_export_20240724_103015/ user@target-server:~/insights-transfer/
```

### Phương Pháp 2: SFTP
```bash
sftp user@target-server
put ~/insights-transfer/insights_export_20240724_103015.zip ~/insights-transfer/
quit
```

### Phương Pháp 3: Cloud Storage
```bash
# Upload lên Google Drive/Dropbox/AWS S3
# Rồi download từ server đích vào ~/insights-transfer/
```

### Phương Pháp 4: USB/Physical Media
```bash
# Copy lên USB
cp ~/insights-transfer/insights_export_20240724_103015.zip /media/usb/

# Chuyển USB sang server khác và copy
cp /media/usb/insights_export_20240724_103015.zip ~/insights-transfer/
```

## 📥 IMPORT DATA (Trên Server Đích)

### 1. Import từ ZIP Package
```bash
cd ~/frappe-bench
python3 ~/insights-transfer/insights_manual_export_import.py import erp.tiqn.local ~/insights-transfer/insights_export_20240724_103015.zip
```

### 2. Import từ JSON Folder
```bash
python3 ~/insights-transfer/insights_manual_export_import.py import erp.tiqn.local ~/insights-transfer/insights_export_20240724_103015/
```

**Output Import:**
```
🚀 Starting import to erp.tiqn.local
📁 Import from: ~/insights-transfer/insights_export_20240724_103015.zip
[10:30:15] INFO: Creating backup before import...
[10:30:16] INFO: Importing 5 records to Insights Dashboard
[10:30:16] INFO: Created: Sales Dashboard
[10:30:17] INFO: Updated: Analytics Dashboard
[10:30:18] INFO: ✅ Imported 5/5 records from insights_dashboard.json
...
✅ Import completed successfully!
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

### Trước Khi Import:
- ✅ **Backup site đích** (script tự động làm)
- ✅ **Đảm bảo Insights app** đã cài đặt
- ✅ **Kiểm tra version compatibility** giữa 2 sites

### Sau Khi Import: 
- ✅ **Test toàn bộ dashboards** hoạt động
- ✅ **Kiểm tra data sources** còn valid
- ✅ **Verify user permissions** trên items mới
- ✅ **Update queries** nếu cần thiết

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