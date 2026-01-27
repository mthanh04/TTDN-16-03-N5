def migrate(cr, version):
    """
    Migration script to set default values for new fields in tai_san
    """
    # Set default gia_mua = 0 for existing records that don't have it
    cr.execute("""
        UPDATE tai_san 
        SET gia_mua = 0 
        WHERE gia_mua IS NULL
    """)
    
    # Set default so_luong = 1 for existing records
    cr.execute("""
        UPDATE tai_san 
        SET so_luong = 1 
        WHERE so_luong IS NULL OR so_luong = 0
    """)
    
    print("Migration completed: Set default values for gia_mua and so_luong")
