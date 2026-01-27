# -*- coding: utf-8 -*-

from . import models
from . import wizard


def pre_init_hook(cr):
    """
    Hook được gọi trước khi module được load/upgrade
    Dùng để cleanup dữ liệu không hợp lệ trước khi Odoo tạo foreign key constraints
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    _logger.info("Running pre_init_hook for phong_hop module...")
    
    # Kiểm tra xem bảng lich_phong_hop đã tồn tại chưa
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'lich_phong_hop'
        )
    """)
    table_exists = cr.fetchone()[0]
    
    if not table_exists:
        _logger.info("Table lich_phong_hop does not exist yet, skipping cleanup")
        return
    
    # Xóa foreign key constraint cũ (nếu có) để tránh conflict
    try:
        cr.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'lich_phong_hop'
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%nguoi_duyet_id%'
        """)
        
        constraints = cr.fetchall()
        for constraint in constraints:
            constraint_name = constraint[0]
            try:
                cr.execute(f"ALTER TABLE lich_phong_hop DROP CONSTRAINT IF EXISTS {constraint_name}")
                _logger.info(f"Dropped old constraint: {constraint_name}")
            except Exception as e:
                _logger.warning(f"Could not drop constraint {constraint_name}: {e}")
    except Exception as e:
        _logger.warning(f"Could not check constraints: {e}")
    
    # Set NULL cho các nguoi_duyet_id không tồn tại
    try:
        cr.execute("""
            UPDATE lich_phong_hop
            SET nguoi_duyet_id = NULL
            WHERE nguoi_duyet_id IS NOT NULL
            AND nguoi_duyet_id NOT IN (SELECT id FROM res_users)
        """)
        affected_rows = cr.rowcount
        if affected_rows > 0:
            _logger.info(f"Fixed {affected_rows} records with invalid nguoi_duyet_id")
        else:
            _logger.info("No invalid nguoi_duyet_id found")
    except Exception as e:
        _logger.error(f"Error fixing invalid nguoi_duyet_id: {e}")
        raise
    
    _logger.info("Pre_init_hook completed successfully")
