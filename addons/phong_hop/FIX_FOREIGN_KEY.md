# Hướng dẫn fix lỗi Foreign Key Constraint Violation

## Lỗi
```
psycopg2.errors.ForeignKeyViolation: insert or update on table "lich_phong_hop" violates foreign key constraint "lich_phong_hop_nguoi_duyet_id_fkey"
DETAIL:  Key (nguoi_duyet_id)=(13) is not present in table "res_users".
```

## Nguyên nhân
Lỗi này xảy ra khi trong bảng `lich_phong_hop` có các bản ghi với `nguoi_duyet_id` trỏ đến user không tồn tại trong bảng `res_users` (có thể do user đã bị xóa).

## Cách fix

### Cách 1: Chạy script SQL trực tiếp (Khuyến nghị)

1. Kết nối đến database PostgreSQL:
```bash
psql -U your_username -d your_database_name
```

2. Chạy các lệnh SQL sau:
```sql
-- Set NULL cho các nguoi_duyet_id không tồn tại
UPDATE lich_phong_hop
SET nguoi_duyet_id = NULL
WHERE nguoi_duyet_id IS NOT NULL
AND nguoi_duyet_id NOT IN (SELECT id FROM res_users);

-- Xóa foreign key constraint cũ
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
        RAISE NOTICE 'Dropped constraint: %', constraint_name;
    END IF;
END $$;
```

3. Sau đó upgrade lại module:
```bash
odoo-bin -u phong_hop -d your_database_name
```

### Cách 2: Chạy từ Odoo shell

1. Chạy Odoo shell:
```bash
odoo-bin shell -d your_database_name
```

2. Trong shell, chạy:
```python
# Fix dữ liệu
env.cr.execute("""
    UPDATE lich_phong_hop
    SET nguoi_duyet_id = NULL
    WHERE nguoi_duyet_id IS NOT NULL
    AND nguoi_duyet_id NOT IN (SELECT id FROM res_users)
""")
env.cr.commit()

# Xóa constraint cũ
env.cr.execute("""
    SELECT constraint_name
    FROM information_schema.table_constraints
    WHERE table_name = 'lich_phong_hop'
    AND constraint_type = 'FOREIGN KEY'
    AND constraint_name LIKE '%nguoi_duyet_id%'
""")
constraints = env.cr.fetchall()
for constraint in constraints:
    constraint_name = constraint[0]
    env.cr.execute("ALTER TABLE lich_phong_hop DROP CONSTRAINT IF EXISTS %s" % constraint_name)
env.cr.commit()
```

3. Sau đó upgrade lại module:
```bash
odoo-bin -u phong_hop -d your_database_name
```

### Cách 3: Sử dụng script SQL file

1. Chạy script SQL từ file `fix_foreign_key.sql`:
```bash
psql -U your_username -d your_database_name -f addons/phong_hop/fix_foreign_key.sql
```

2. Sau đó upgrade lại module:
```bash
odoo-bin -u phong_hop -d your_database_name
```

## Lưu ý
- Sau khi fix, foreign key constraint sẽ được tạo lại tự động với `ondelete='set null'` khi upgrade module
- Module đã được cập nhật để tự động set NULL khi user bị xóa trong tương lai
