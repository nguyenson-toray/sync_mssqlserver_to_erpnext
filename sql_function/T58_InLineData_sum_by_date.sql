-- Query tổng hợp dữ liệu từ bảng T58_InLineData theo line và date
-- Lọc dữ liệu trong 14 ngày gần nhất, tính tổng qty và qty_ok, 
-- và tính tỷ lệ lỗi (defect ratio) làm tròn 2 chữ số thập phân

SELECT 
    line,                              -- Mã dây chuyền sản xuất
    DATE(date) as production_date,     -- Ngày sản xuất (chỉ lấy phần date, bỏ time)
    SUM(qty) as total_qty,             -- Tổng số lượng sản phẩm được kiểm tra
    SUM(qty_ok) as total_qty_ok,       -- Tổng số lượng sản phẩm đạt chất lượng
    ROUND(                             -- Tính tỷ lệ lỗi và làm tròn 2 chữ số thập phân
        CASE 
            WHEN SUM(qty) > 0 THEN     -- Kiểm tra chia cho 0
                (SUM(qty) - SUM(qty_ok)) / SUM(qty) 
            ELSE 0 
        END, 
        2
    ) AS defect_ratio                  -- Tỷ lệ lỗi = (qty - qty_ok) / qty
FROM T58_InLineData
WHERE 
    date >= CURDATE() - INTERVAL 14 DAY  -- Lọc dữ liệu trong 14 ngày gần nhất
    AND date < CURDATE()                 -- Không bao gồm ngày hiện tại (chỉ lấy dữ liệu đã hoàn thành)
    AND qty IS NOT NULL                  -- Loại bỏ các bản ghi không có dữ liệu qty
    AND qty > 0                          -- Chỉ lấy các bản ghi có qty > 0
GROUP BY 
    line,                                -- Nhóm theo dây chuyền sản xuất
    DATE(date)                           -- Nhóm theo ngày (bỏ qua giờ)
ORDER BY 
    line,                                -- Sắp xếp theo mã dây chuyền
    production_date DESC                 -- Sau đó sắp xếp theo ngày giảm dần (mới nhất trước)

-- Giải thích các trường kết quả:
-- line: Mã định danh của dây chuyền sản xuất
-- production_date: Ngày sản xuất (định dạng YYYY-MM-DD)
-- total_qty: Tổng số lượng sản phẩm được kiểm tra trong ngày tại dây chuyền đó
-- total_qty_ok: Tổng số lượng sản phẩm đạt chất lượng trong ngày tại dây chuyền đó  
-- defect_ratio: Tỷ lệ lỗi (0.00 = 0%, 1.00 = 100%), giá trị càng thấp càng tốt