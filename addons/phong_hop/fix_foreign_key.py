#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để fix lỗi foreign key constraint violation
Chạy script này từ Odoo shell:
    odoo-bin shell -d your_database_name
    Sau đó chạy: exec(open('addons/phong_hop/fix_foreign_key.py').read())
"""

import logging
_logger = logging.getLogger(__name__)

def fix_foreign_key_violation(env):
    """
    Fix foreign key constraint violation bằng cách:
    1. Set NULL cho các nguoi_duyet_id không tồn tại trong res_users
    2. Xóa foreign key constraint cũ để Odoo tạo lại với ondelete='set null'
    """
    cr = env.cr
    
    try:
        # Bước 1: Set NULL cho các nguoi_duyet_id không tồn tại
        cr.execute("""
            UPDATE lich_phong_hop
            SET nguoi_duyet_id = NULL
            WHERE nguoi_duyet_id IS NOT NULL
            AND nguoi_duyet_id NOT IN (SELECT id FROM res_users)
        """)
        affected_rows = cr.rowcount
        _logger.info("Fixed %d records with invalid nguoi_duyet_id", affected_rows)
        
        # Bước 2: Xóa foreign key constraint cũ
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
                cr.execute("ALTER TABLE lich_phong_hop DROP CONSTRAINT IF EXISTS %s" % constraint_name)
                _logger.info("Dropped constraint: %s", constraint_name)
            except Exception as e:
                _logger.warning("Could not drop constraint %s: %s", constraint_name, e)
        
        cr.commit()
        _logger.info("Successfully fixed foreign key constraint violation")
        return True
        
    except Exception as e:
        _logger.error("Error fixing foreign key constraint: %s", e)
        cr.rollback()
        return False

# Chạy script nếu được gọi trực tiếp từ Odoo shell
if __name__ == '__main__':
    # Lấy environment từ context
    import odoo
    from odoo import api, SUPERUSER_ID
    
    # Giả sử đã có env trong context (khi chạy từ shell)
    # Nếu không, cần tạo env:
    # env = api.Environment(cr, SUPERUSER_ID, {})
    pass

# Để chạy từ Odoo shell:
# fix_foreign_key_violation(env)
