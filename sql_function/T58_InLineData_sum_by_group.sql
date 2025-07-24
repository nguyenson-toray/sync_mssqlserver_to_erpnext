-- Query tổng hợp dữ liệu chất lượng từ bảng T58_InLineData theo quy trình
-- Join với T59_TransInLine để lấy thông tin mô tả quy trình
-- Tính tổng qty, qty_ok, qty_ng và tỷ lệ lỗi trong 14 ngày gần nhất

SELECT 
    t58.line,                                    -- Mã dây chuyền sản xuất
    DATE(t58.date) as production_date,          -- Ngày sản xuất (chỉ lấy phần date, bỏ time)
    t58.process_no,                             -- Mã số quy trình sản xuất
    t59.process_viet,                           -- Tên quy trình bằng tiếng Việt (từ bảng T59_TransInLine)
    t59.process_jpn,                            -- Tên quy trình bằng tiếng Nhật (từ bảng T59_TransInLine)
    
    SUM(t58.qty) as total_qty,                  -- Tổng số lượng sản phẩm được kiểm tra
    SUM(t58.qty_ok) as total_qty_ok,            -- Tổng số lượng sản phẩm đạt chất lượng
    
    -- Tính số lượng không đạt = tổng qty - tổng qty_ok
    (SUM(t58.qty) - SUM(t58.qty_ok)) as qty_ng,
    
    -- Tính tỷ lệ lỗi và làm tròn 2 chữ số thập phân
    ROUND(
        CASE 
            WHEN SUM(t58.qty) > 0 THEN          -- Kiểm tra chia cho 0
                (SUM(t58.qty) - SUM(t58.qty_ok)) / SUM(t58.qty) 
            ELSE 0 
        END, 
        2
    ) AS defect_ratio                           -- Tỷ lệ lỗi = (qty - qty_ok) / qty

FROM T58_InLineData t58
LEFT JOIN T59_TransInLine t59 ON (
    t58.item_id = t59.item_id                   -- Join theo item_id (mã sản phẩm)
    AND t58.process_no = t59.process_id         -- Join theo process_no từ T58 với process_id từ T59
)
WHERE 
    t58.date >= CURDATE() - INTERVAL 14 DAY     -- Lọc dữ liệu trong 14 ngày gần nhất
    AND t58.date < CURDATE()                    -- Không bao gồm ngày hiện tại (chỉ lấy dữ liệu đã hoàn thành)
    AND t58.qty IS NOT NULL                     -- Loại bỏ các bản ghi không có dữ liệu qty
    AND t58.qty > 0                             -- Chỉ lấy các bản ghi có qty > 0 (có dữ liệu thực tế)

GROUP BY 
    t58.line,                                   -- Nhóm theo dây chuyền sản xuất
    DATE(t58.date),                             -- Nhóm theo ngày sản xuất (bỏ qua giờ)
    t58.process_no,                             -- Nhóm theo mã quy trình sản xuất
    t59.process_viet,                           -- Nhóm theo tên quy trình tiếng Việt
    t59.process_jpn                             -- Nhóm theo tên quy trình tiếng Nhật

ORDER BY 
    t58.line,                                   -- Sắp xếp theo mã dây chuyền
    production_date DESC,                       -- Sau đó theo ngày giảm dần (mới nhất trước)
    t58.process_no                              -- Cuối cùng theo mã quy trình

-- Giải thích các trường kết quả:
-- line: Mã định danh của dây chuyền sản xuất
-- production_date: Ngày sản xuất (định dạng YYYY-MM-DD)
-- process_no: Mã số quy trình sản xuất trong dây chuyền
-- process_viet: Tên mô tả quy trình bằng tiếng Việt (lấy từ bảng T59_TransInLine)
-- process_jpn: Tên mô tả quy trình bằng tiếng Nhật (lấy từ bảng T59_TransInLine)
-- total_qty: Tổng số lượng sản phẩm được kiểm tra trong ngày tại quy trình đó
-- total_qty_ok: Tổng số lượng sản phẩm đạt chất lượng trong ngày tại quy trình đó
-- qty_ng: Tổng số lượng sản phẩm không đạt chất lượng (qty_ng = total_qty - total_qty_ok)
-- defect_ratio: Tỷ lệ lỗi (0.00 = 0%, 1.00 = 100%), giá trị càng thấp càng tốt

-- Lưu ý về JOIN:
-- Sử dụng LEFT JOIN để đảm bảo không mất dữ liệu từ T58_InLineData 
-- ngay cả khi không tìm thấy thông tin mô tả trong T59_TransInLine
-- Điều kiện JOIN: t58.item_id = t59.item_id AND t58.process_no = t59.process_id