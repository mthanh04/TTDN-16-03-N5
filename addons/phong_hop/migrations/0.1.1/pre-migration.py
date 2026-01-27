# -*- coding: utf-8 -*-
"""
Migration script to fix foreign key constraint violation
Fixes records in lich_phong_hop that reference non-existent users
"""

def migrate(cr, version):
    """
    Fix foreign key constraint violation by setting NULL for nguoi_duyet_id
    that reference non-existent users
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    # Drop existing foreign key constraint if it exists (to allow recreation with ondelete='set null')
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
                cr.execute("ALTER TABLE lich_phong_hop DROP CONSTRAINT IF EXISTS %s" % constraint_name)
                _logger.info("Dropped constraint: %s", constraint_name)
            except Exception as e:
                _logger.warning("Could not drop constraint %s: %s", constraint_name, e)
    except Exception as e:
        _logger.warning("Could not check constraints: %s", e)
    
    # Find and fix records with invalid nguoi_duyet_id
    try:
        cr.execute("""
            UPDATE lich_phong_hop
            SET nguoi_duyet_id = NULL
            WHERE nguoi_duyet_id IS NOT NULL
            AND nguoi_duyet_id NOT IN (SELECT id FROM res_users)
        """)
        affected_rows = cr.rowcount
        if affected_rows > 0:
            _logger.info("Fixed %d records with invalid nguoi_duyet_id", affected_rows)
        # No need to commit - Odoo handles transaction management
    except Exception as e:
        _logger.error("Error fixing invalid nguoi_duyet_id: %s", e)
        # Don't rollback - let Odoo handle it
        raise
