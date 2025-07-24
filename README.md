# MSSQL to MariaDB Data Synchronization

Tool đồng bộ dữ liệu từ MSSQL Server sang MariaDB với hỗ trợ Full/Incremental sync modes và export cấu trúc bảng.
cd /home/sonnt/frappe-bench/sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext && python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python db_sync.py
## Prerequisites

**1. Install Python Dependencies:**
```bash
pip3 install -r requirements.txt
# Or via apt for mysql connector:
sudo apt install python3-mysql.connector
```

**2. Install SQL Server Tools:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y freetds-bin freetds-dev

# Test connection
tsql -S 10.0.1.4 -U sa -P 'itT0ray$' -D Production
```

**3. Database Info:**
- **MSSQL**: 10.0.1.4, DB: Production, User: sa
- **MariaDB**: localhost, DB: Production (tự động tạo), User: root

## Hướng Dẫn Chạy Lệnh Python

### 1. Cấu hình trước khi chạy

**Kiểm tra config.py:**
```python
# Mở file config.py và kiểm tra:
# - Database credentials
# - Table sync configuration
# - Sync modes và column mapping
```

### 2. Các lệnh sync cơ bản

**Sync tất cả tables (theo config):**
```bash
# Chạy sync với mode mặc định (full/incremental theo config)
python3 db_sync.py

# Enable debug logging
DEBUG=1 python3 db_sync.py
```

**Force full sync (bỏ qua incremental timestamps):**
```bash
# Reset tất cả timestamps và chạy full sync
python3 db_sync.py --force-full

# Với debug
DEBUG=1 python3 db_sync.py --force-full
```

### 3. Sync table cụ thể

**Sync 1 table:**
```bash
# Sync table T50_InspectionData theo mode đã config
python3 db_sync.py --table T50_InspectionData

# Sync T52_ProductItem
python3 db_sync.py --table T52_ProductItem

# Sync T58_InLineData (table lớn - thường dùng incremental)
python3 db_sync.py --table T58_InLineData
```

**Kết hợp options:**
```bash
# Force full sync cho 1 table cụ thể
python3 db_sync.py --table T50_InspectionData --force-full

# Với debug logging
DEBUG=1 python3 db_sync.py --table T58_InLineData --force-full
```

### 4. Monitoring và Debug

**Xem log real-time:**
```bash
# Chạy sync và theo dõi log
python3 db_sync.py & tail -f sync.log

# Chỉ xem log
tail -f sync.log

# Xem log errors
grep ERROR sync.log
```

**Kiểm tra kết quả sync:**
```bash
# Xem last sync timestamps
cat last_sync.json

# Xem log summary
tail -20 sync.log | grep "Sync completed"
```

### 5. Environment Variables (Optional)

```bash
export MSSQL_SERVER="10.0.1.4"
export MSSQL_USERNAME="sa" 
export MSSQL_PASSWORD="itT0ray$"
export MARIADB_HOST="localhost"
export MARIADB_USER="root"
export MARIADB_PASSWORD="T0ray25#"
export SYNC_BATCH_SIZE="1000"
export DEBUG="1"
```

## Tính Năng Chính

- **Dual sync modes**: Full (drop/recreate) hoặc Incremental (upsert)
- **Column mapping**: Đổi tên columns (MSSQL → MariaDB)
- **Selective sync**: Chỉ sync tables/columns được chọn
- **Batch processing**: Tối ưu performance với batch size
- **Auto data cleaning**: Tự động clean và validate dữ liệu
- **Progress tracking**: Theo dõi tiến trình real-time
- **Error handling**: Tiếp tục sync dù có table lỗi
- **Timestamp tracking**: Tự động track cho incremental sync

## Data Types & State Files

**MSSQL → MariaDB Conversion:**
```
int → INT, datetime → DATETIME, varchar(n) → VARCHAR(n)
bit → BOOLEAN, money → DECIMAL(19,4), text → TEXT
```

**Generated Files:**
- `sync.log` - Chi tiết quá trình sync
- `last_sync.json` - Timestamps cho incremental sync

## Configuration (config.py)

**Cấu trúc config cho mỗi table:**
```python
'table_name': {
    'sync': True,                          # Bật sync
    'sync_mode': 'full' or 'incremental',  # Chế độ sync
    'timestamp_column': 'X02',             # Column timestamp (cho incremental)
    'primary_key': 'ID',                   # Primary key (cho upsert)
    'condition': "X02 > '2025-01-01'",     # Filter điều kiện
    'columns': None or ['col1', 'col2'],   # Columns sync (None = all)
    'column_mapping': {                    # Đổi tên column
        '2nd': 'inspection_type',          # MSSQL → MariaDB
        'X02': 'inspection_date'
    }
}
```

**Ví dụ thực tế:**
```python
# Table lớn - dùng incremental
'T58_InLineData': {
    'sync': True,
    'sync_mode': 'incremental',
    'timestamp_column': 'X02',
    'primary_key': 'ID'
},

# Table nhỏ - dùng full sync
'T52_ProductItem': {
    'sync': True,
    'sync_mode': 'full',
    'column_mapping': {
        '2nd': 'inspection_type'
    }
}
```

## Cơ Chế Đồng Bộ (Sync Mechanism)

### 1. Full Sync Mode (`sync_mode: 'full'`)

**Cách hoạt động:**
- Xóa hoàn toàn table hiện tại (DROP TABLE)
- Tạo lại table mới với cấu trúc từ MSSQL
- Import toàn bộ dữ liệu từ đầu

**Khi nào sử dụng:**
- Bảng nhỏ (< 10,000 records)
- Lần sync đầu tiên
- Cần đảm bảo dữ liệu hoàn toàn chính xác
- Cấu trúc bảng thay đổi

**Ưu điểm:**
- Đơn giản, không cần quản lý trạng thái
- Đảm bảo dữ liệu 100% chính xác
- Tự động dọn dẹp dữ liệu cũ

**Nhược điểm:**
- Chậm với bảng lớn
- Mất dữ liệu MariaDB-specific (indexes, triggers)
- Downtime khi sync

### 2. Incremental Sync Mode (`sync_mode: 'incremental'`)

**Cách hoạt động:**
- Kiểm tra timestamp lần sync cuối từ `last_sync.json`
- Chỉ sync dữ liệu có `timestamp_column > last_sync_time`
- Sử dụng UPSERT (INSERT...ON DUPLICATE KEY UPDATE)
- Cập nhật timestamp sau khi sync thành công

**Khi nào sử dụng:**
- Bảng lớn (> 10,000 records)
- Sync thường xuyên (hàng giờ/ngày)
- Production environment
- Cần preserve dữ liệu existing

**Ưu điểm:**
- Nhanh, chỉ sync dữ liệu thay đổi
- Không downtime
- Tiết kiệm bandwidth và storage
- Preserve dữ liệu existing

**Nhược điểm:**
- Phức tạp hơn, cần primary key
- Phụ thuộc vào timestamp column
- Có thể miss dữ liệu nếu timestamp không chính xác

### 3. Timestamp Column (`timestamp_column`)

**Vai trò quan trọng trong Incremental Sync:**
```python
'timestamp_column': 'X02'  # Column chứa thời gian update/create
```

**Cách hoạt động:**
1. **Lần sync đầu**: Sync toàn bộ, lưu MAX(X02) vào `last_sync.json`
2. **Lần sync tiếp theo**: Chỉ sync WHERE X02 > last_sync_time
3. **Sau sync**: Cập nhật last_sync_time = MAX(X02) mới

**Yêu cầu:**
- Column phải có kiểu datetime/timestamp
- Tự động update khi record thay đổi
- Không được NULL
- Tăng dần theo thời gian

### 4. Workflow Commands

**Lần đầu setup:**
```bash
# 1. Cài đặt dependencies
pip3 install -r requirements.txt

# 2. Test connection
tsql -S 10.0.1.4 -U sa -P 'itT0ray$' -D Production

# 3. Chạy full sync lần đầu
python3 db_sync.py --force-full
```

**Sync hàng ngày:**
```bash
# Incremental sync (chỉ sync data mới)
python3 db_sync.py

# Nếu cần debug
DEBUG=1 python3 db_sync.py
```

**Khi có vấn đề:**
```bash
# Reset và sync lại toàn bộ
rm -f last_sync.json
python3 db_sync.py --force-full

# Sync từng table để debug
python3 db_sync.py --table T50_InspectionData --force-full
```

### 5. Sync Process Flow

#### Full Sync:
```
START → Connect DB → DROP TABLE → CREATE TABLE → INSERT ALL DATA → END
```

#### Incremental Sync:
```
START → Connect DB → Check last_sync.json → CREATE TABLE (if not exists) 
     → Query WHERE timestamp > last_sync → UPSERT new data 
     → Update last_sync.json → END
```

### 6. Các Lệnh Thường Dùng

**Kiểm tra trạng thái:**
```bash
# Xem tables đã sync
cat last_sync.json

# Đếm rows trong MariaDB
mysql -u root -p'T0ray25#' -e "USE Production; SELECT 'T50_InspectionData', COUNT(*) FROM T50_InspectionData;"

# Xem log lỗi gần đây
tail -50 sync.log | grep ERROR
```

**Reset và troubleshoot:**
```bash
# Xóa timestamps (force full sync lần sau)
rm last_sync.json

# Xóa table và sync lại
mysql -u root -p'T0ray25#' -e "USE Production; DROP TABLE T50_InspectionData;"
python3 db_sync.py --table T50_InspectionData --force-full

# Test sync 1 table nhỏ trước
python3 db_sync.py --table T52_ProductItem --force-full
```

## Export Cấu Trúc Tables (Sau Khi Sync)

**Script export cấu trúc MariaDB:**
```bash
# Export tất cả tables đã sync (JSON, SQL, Report)
python3 export_table_structure.py

# Chỉ export định dạng JSON
python3 export_table_structure.py --format json

# Chỉ export định dạng SQL (CREATE TABLE statements)
python3 export_table_structure.py --format sql

# Chỉ export summary report
python3 export_table_structure.py --format report

# Export tables cụ thể
python3 export_table_structure.py --tables T50_InspectionData T52_ProductItem

# Xem demo và examples
python3 example_export_usage.py
```

**Output files được tạo:**
- `mariadb_structures_YYYYMMDD_HHMMSS.json` - Cấu trúc đầy đủ định dạng JSON
- `mariadb_structures_YYYYMMDD_HHMMSS.sql` - CREATE TABLE statements
- `sync_report_YYYYMMDD_HHMMSS.md` - Báo cáo tổng kết định dạng Markdown

## Lưu Ý & Best Practices

**Ở Production:**
- Dùng incremental sync cho tables lớn (> 10K rows)
- Schedule sync vào giờ ít tải (ban đêm)
- Monitor `sync.log` để catch lỗi sớm
- Backup `last_sync.json` trước khi thay đổi config

**Security:**
- Dùng environment variables cho passwords
- Đặt quyền MariaDB user chỉ cần thiết (CREATE, DROP, INSERT, UPDATE)

**Performance:**
- Batch size mặc định: 1000 rows
- Tables > 100K rows nên dùng incremental mode
- Kiểm tra indexes trên timestamp_column

## Troubleshooting

**Lỗi thường gặp:**
```bash
# "0 rows synced" dù MSSQL có data
# → Kiểm tra column mapping và data types
python3 db_sync.py --table T52_ProductItem --force-full

# "Connection refused"
# → Kiểm tra MSSQL server và credentials
tsql -S 10.0.1.4 -U sa -P 'itT0ray$' -D Production

# "Table not found"
# → Kiểm tra table name trong config.py
grep -A 5 "T50_InspectionData" config.py

# "Duplicate key error"
# → Kiểm tra primary_key config
# → Xóa table và sync lại
DROP TABLE T50_InspectionData;
python3 db_sync.py --table T50_InspectionData --force-full
```

**Debug steps:**
1. Kiểm tra config: `grep -A 10 "table_name" config.py`
2. Test connection: `tsql -S 10.0.1.4 -U sa -P 'password'`
3. Chạy với debug: `DEBUG=1 python3 db_sync.py --table XXX`
4. Kiểm tra log: `tail -50 sync.log`
5. Reset nếu cần: `rm last_sync.json && python3 db_sync.py --force-full`
