# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migration script để thêm các cột mới vào bảng nhan_vien
    Chạy script này khi upgrade module từ version cũ lên 0.1.0
    """
    # Kiểm tra và thêm cột user_id nếu chưa tồn tại
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='nhan_vien' AND column_name='user_id'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE nhan_vien 
            ADD COLUMN user_id INTEGER REFERENCES res_users(id) ON DELETE SET NULL
        """)
    
    # Kiểm tra và thêm cột chuc_vu_id nếu chưa tồn tại
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='nhan_vien' AND column_name='chuc_vu_id'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE nhan_vien 
            ADD COLUMN chuc_vu_id INTEGER REFERENCES chuc_vu(id) ON DELETE SET NULL
        """)
    
    # Kiểm tra và thêm cột trang_thai nếu chưa tồn tại
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='nhan_vien' AND column_name='trang_thai'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE nhan_vien 
            ADD COLUMN trang_thai VARCHAR
        """)
        # Cập nhật giá trị mặc định cho các bản ghi cũ
        cr.execute("""
            UPDATE nhan_vien 
            SET trang_thai = 'dang_lam' 
            WHERE trang_thai IS NULL
        """)
