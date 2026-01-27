-- Script SQL để thêm các cột mới vào bảng nhan_vien
-- Chạy script này trực tiếp trong database nếu gặp lỗi "column does not exist"

-- Thêm cột user_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='nhan_vien' AND column_name='user_id'
    ) THEN
        ALTER TABLE nhan_vien 
        ADD COLUMN user_id INTEGER REFERENCES res_users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Thêm cột chuc_vu_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='nhan_vien' AND column_name='chuc_vu_id'
    ) THEN
        ALTER TABLE nhan_vien 
        ADD COLUMN chuc_vu_id INTEGER REFERENCES chuc_vu(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Thêm cột trang_thai
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='nhan_vien' AND column_name='trang_thai'
    ) THEN
        ALTER TABLE nhan_vien 
        ADD COLUMN trang_thai VARCHAR;
        
        -- Cập nhật giá trị mặc định cho các bản ghi cũ
        UPDATE nhan_vien 
        SET trang_thai = 'dang_lam' 
        WHERE trang_thai IS NULL;
    END IF;
END $$;
