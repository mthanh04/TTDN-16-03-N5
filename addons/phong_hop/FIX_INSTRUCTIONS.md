# HƯỚNG DẪN FIX LỖI FOREIGN KEY CONSTRAINT (DOCKER VERSION)

## ✅ ĐÃ FIX TỰ ĐỘNG!

Module đã được cập nhật với **pre_init_hook** tự động cleanup dữ liệu không hợp lệ.

## Cách sử dụng

### Bước 1: Restart Odoo và Upgrade Module

Chỉ cần chạy lệnh upgrade module như bình thường:

```bash
# Nếu dùng odoo-bin trực tiếp
./odoo-bin -u phong_hop -d <tên_database>

# Hoặc nếu Odoo chạy trong Docker
docker-compose restart odoo
# Sau đó vào giao diện web -> Apps -> Tìm "Quản lý Phòng họp" -> Click Upgrade
```

### Bước 2: Kiểm tra Log

Trong log của Odoo, bạn sẽ thấy các thông báo:
```
INFO db_user odoo.addons.phong_hop: Running pre_init_hook for phong_hop module...
INFO db_user odoo.addons.phong_hop: Fixed X records with invalid nguoi_duyet_id
INFO db_user odoo.addons.phong_hop: Pre_init_hook completed successfully
```

## Giải thích

**Pre-init hook** là gì?
- Là một function được Odoo tự động gọi **TRƯỚC KHI** load module
- Chạy trước khi Odoo tạo foreign key constraints
- Tự động cleanup dữ liệu không hợp lệ

**Hook này làm gì?**
1. ✅ Kiểm tra xem bảng `lich_phong_hop` đã tồn tại chưa
2. ✅ Xóa foreign key constraint cũ (nếu có)
3. ✅ Set `nguoi_duyet_id = NULL` cho các bản ghi có user ID không tồn tại
4. ✅ Để Odoo tạo lại constraint mới với `ON DELETE SET NULL`

## Kết quả

Sau khi upgrade:
- ✅ Lỗi foreign key constraint đã được fix
- ✅ Module load thành công
- ✅ Các bản ghi cũ có `nguoi_duyet_id` không hợp lệ được set về NULL
- ✅ Các bản ghi khác (phòng họp, thời gian, người đặt...) vẫn giữ nguyên

## Nếu Vẫn Muốn Chạy SQL Thủ Công (Docker)

Nếu bạn muốn chạy SQL trực tiếp trong Docker container:

```bash
# Tìm tên container PostgreSQL
docker ps | grep postgres

# Kết nối vào PostgreSQL container
docker exec -it <postgres_container_name> psql -U <username> -d <database_name>

# Hoặc một lệnh
docker exec -it <postgres_container_name> psql -U odoo -d db_user
```

Sau đó paste các lệnh SQL:
```sql
-- Set NULL cho các nguoi_duyet_id không hợp lệ
UPDATE lich_phong_hop
SET nguoi_duyet_id = NULL
WHERE nguoi_duyet_id IS NOT NULL
AND nguoi_duyet_id NOT IN (SELECT id FROM res_users);

-- Xóa constraint cũ
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'lich_phong_hop'::regclass
    AND contype = 'f'
    AND conname LIKE '%nguoi_duyet_id%';
    
    IF constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE lich_phong_hop DROP CONSTRAINT IF EXISTS ' || constraint_name;
    END IF;
END $$;
```

Sau đó thoát (gõ `\q`) và restart Odoo.

## Thay Đổi Trong Code

### 1. File: `__init__.py`
Thêm function `pre_init_hook()` để tự động cleanup dữ liệu

### 2. File: `__manifest__.py`
- Version: `0.1.1` → `0.1.2`
- Thêm: `'pre_init_hook': 'pre_init_hook'`

## Lưu Ý
- Hook này **LUÔN CHẠY** mỗi khi upgrade module
- Hoàn toàn an toàn - chỉ fix những bản ghi có vấn đề
- Không ảnh hưởng đến dữ liệu hợp lệ
