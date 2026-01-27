-- Script SQL để fix lỗi foreign key constraint violation
-- Chạy script này trong database để fix dữ liệu trước khi upgrade module

-- Bước 1: Set NULL cho các nguoi_duyet_id không tồn tại trong res_users
UPDATE lich_phong_hop
SET nguoi_duyet_id = NULL
WHERE nguoi_duyet_id IS NOT NULL
AND nguoi_duyet_id NOT IN (SELECT id FROM res_users);

-- Bước 2: Xóa foreign key constraint cũ (nếu có)
-- Lưu ý: Thay thế 'lich_phong_hop_nguoi_duyet_id_fkey' bằng tên constraint thực tế trong database của bạn
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    -- Tìm tên constraint
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'lich_phong_hop'::regclass
    AND contype = 'f'
    AND conname LIKE '%nguoi_duyet_id%';
    
    -- Xóa constraint nếu tồn tại
    IF constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE lich_phong_hop DROP CONSTRAINT IF EXISTS ' || constraint_name;
        RAISE NOTICE 'Dropped constraint: %', constraint_name;
    END IF;
END $$;
