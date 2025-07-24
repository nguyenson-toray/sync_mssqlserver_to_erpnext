# Database Sync Cron Jobs Management

Hướng dẫn quản lý cron jobs tự động đồng bộ dữ liệu từ SQL Server sang MariaDB/ERPNext.

## Tổng quan

Script `cron_manager.py` quản lý các cron jobs để tự động chạy đồng bộ dữ liệu theo lịch trình đã định.

## Cấu hình mặc định

- **Thời gian chạy**: 10:00, 13:00, 18:00, 23:00 hàng ngày
- **Chế độ đồng bộ**: Incremental (chỉ đồng bộ dữ liệu mới/thay đổi)
- **Log file**: `/var/log/db_sync.log`

## Các lệnh cơ bản

### 1. Thiết lập cron jobs

```bash
# Thiết lập với thời gian mặc định (10:00, 13:00, 18:00, 23:00)
venv/bin/python cron_manager.py setup

# Thiết lập với thời gian tùy chỉnh
venv/bin/python cron_manager.py setup --times 09:00 12:00 15:00 21:00
```

### 2. Xem danh sách cron jobs hiện tại

```bash
venv/bin/python cron_manager.py list
```

### 3. Xóa tất cả cron jobs đồng bộ

```bash
venv/bin/python cron_manager.py remove
```

### 4. Xem cron jobs toàn hệ thống

```bash
crontab -l
```

## Cấu trúc Cron Jobs

Mỗi cron job có định dạng:
```
MM HH * * * /path/to/venv/bin/python /path/to/db_sync.py >> /var/log/db_sync.log 2>&1
```

Ví dụ:
```
00 10 * * * /home/sonnt/frappe-bench/sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/venv/bin/python /home/sonnt/frappe-bench/sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/db_sync.py >> /var/log/db_sync.log 2>&1
```

## Chế độ đồng bộ

### Incremental Sync (Mặc định)
- Chỉ đồng bộ dữ liệu mới hoặc đã thay đổi
- Dựa trên timestamp column (X02 cho hầu hết các bảng)
- Nhanh hơn và ít tốn tài nguyên

### Full Sync
- Đồng bộ toàn bộ dữ liệu
- Sử dụng khi cần khôi phục hoàn toàn
- Chậm hơn nhưng đảm bảo tính toàn vẹn

## Cấu hình bảng đồng bộ

Trong `config.py`, mỗi bảng có cấu hình:

```python
'T50_InspectionData': {
    'sync': True,
    'sync_mode': 'incremental',  # hoặc 'full'
    'timestamp_column': 'X02',   # cột timestamp để theo dõi
    'primary_key': 'ID',
    'column_mapping': {
        'X02': 'date',           # ánh xạ tên cột
        'X01': 'line',
        # ...
    }
}
```

## Monitoring và Logs

### Xem logs real-time
```bash
tail -f /var/log/db_sync.log
```

### Xem logs của lần chạy cuối
```bash
tail -100 /var/log/db_sync.log
```

### Kiểm tra status cron service
```bash
systemctl status cron
```

### Xem cron logs hệ thống
```bash
grep CRON /var/log/syslog | tail -20
```

## Troubleshooting

### 1. Cron jobs không chạy

Kiểm tra:
```bash
# Xem cron service có đang chạy không
systemctl status cron

# Khởi động lại cron service
sudo systemctl restart cron

# Kiểm tra cron logs
grep CRON /var/log/syslog
```

### 2. Script không tìm thấy file

Đảm bảo đường dẫn đầy đủ trong cron job:
- Virtual environment: `/full/path/to/venv/bin/python`
- Script path: `/full/path/to/db_sync.py`

### 3. Permission issues

```bash
# Đảm bảo script có quyền thực thi
chmod +x cron_manager.py
chmod +x db_sync.py

# Tạo log file nếu chưa có
sudo touch /var/log/db_sync.log
sudo chown $USER:$USER /var/log/db_sync.log
```

### 4. Database connection issues

Kiểm tra:
- Cấu hình database trong `config.py`
- Network connectivity
- Database credentials
- Virtual environment có đầy đủ packages

## Ví dụ sử dụng

### Thiết lập lịch làm việc thông thường
```bash
# Chạy 4 lần/ngày: sáng, trưa, chiều, tối
venv/bin/python cron_manager.py setup --times 08:00 12:00 16:00 20:00
```

### Thiết lập cho môi trường test (chạy thường xuyên hơn)
```bash
# Chạy mỗi 2 tiếng từ 8h-18h
venv/bin/python cron_manager.py setup --times 08:00 10:00 12:00 14:00 16:00 18:00
```

### Thiết lập cho cuối tuần (ít hơn)
```bash
# Chỉ chạy 2 lần: sáng và tối
venv/bin/python cron_manager.py setup --times 09:00 21:00
```

## Best Practices

1. **Backup trước khi thiết lập**
   ```bash
   # Backup crontab hiện tại
   crontab -l > crontab_backup.txt
   ```

2. **Test trước khi deploy**
   ```bash
   # Chạy sync manually để test
   venv/bin/python db_sync.py
   ```

3. **Monitor logs thường xuyên**
   ```bash
   # Thiết lập log rotation để không đầy disk
   sudo logrotate -f /etc/logrotate.conf
   ```

4. **Cấu hình email notification** (optional)
   - Thêm `MAILTO=your-email@domain.com` vào đầu crontab
   - Cron sẽ gửi email nếu có lỗi

## Cấu hình nâng cao

### Chạy với user khác
```bash
# Chỉnh sửa crontab của user khác
sudo crontab -u username -e
```

### Parallel execution prevention
Script tự động kiểm tra để tránh chạy đồng thời nhiều instances.

### Custom log location
Sửa đổi đường dẫn log trong `cron_manager.py`:
```python
cron_line = f"{minute} {hour} * * * {self.venv_python} {self.sync_script} >> /path/to/custom.log 2>&1"
```

## Liên hệ

Nếu có vấn đề, kiểm tra:
1. Logs trong `/var/log/db_sync.log` 
2. System cron logs: `/var/log/syslog`
3. Database connectivity
4. Virtual environment setup