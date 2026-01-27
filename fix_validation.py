file_path = r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\tai_san\models\phieu_muon_tai_san_line.py'

# Read
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add recompute call before validation
content = content.replace(
    '''    @api.constrains('tai_san_id', 'so_luong')
    def _check_tai_san_availability(self):
        """Kiểm tra tài sản có thể mượn không"""
        for record in self:
            ts = record.tai_san_id
            
            # Kiểm tra số lượng > 0
            if record.so_luong <= 0:''',
    '''    @api.constrains('tai_san_id', 'so_luong')
    def _check_tai_san_availability(self):
        """Kiểm tra tài sản có thể mượn không"""
        for record in self:
            ts = record.tai_san_id
            
            # FORCE RECOMPUTE để lấy giá trị mới nhất
            ts._compute_so_luong_muon()
            
            # Kiểm tra số lượng > 0
            if record.so_luong <= 0:'''
)

# Write
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Added recompute trigger!")
