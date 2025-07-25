# Insights Export/Import

Export/import dữ liệu Insights giữa các ERPNext sites.

## Sử dụng nhanh

### Export
```bash
cd /home/sonnt/frappe-bench
./sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/insights_manual_export_import/bench_export.sh erp-sonnt.tiqn.local
```

### Transfer
```bash
scp insights_export_*.zip user@target-server:~/
```

### Import 
```bash
cd /home/sonnt/frappe-bench
./sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/insights_manual_export_import/bench_import.sh ~/insights_export_20250725_081227/
```

Hoặc từ ZIP:
```bash
./sync_mssqlserver_to_erpnext/sync_mssqlserver_to_erpnext/insights_manual_export_import/bench_import.sh ~/insights_export_*.zip
```

## Files được export
- Insights Data Source
- Insights Workbook  
- Insights Query v3
- Insights Chart v3
- Insights Dashboard v3
- Insights Dashboard Chart v3

## Lỗi thường gặp

**Site not found:** Kiểm tra tên site với `ls sites/`

**DocType not found:** Cài Insights app: `bench --site your-site install-app insights`

**Permission denied:** `chmod +x *.sh`

## Verify sau import
1. Login ERPNext → Insights app
2. Kiểm tra Dashboards, Charts, Queries hiển thị đúng