import re

file_path = r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\tai_san\models\tai_san.py'

# Read
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix indentation - move "def action_recalculate_quantity" to proper level
# Find and replace the problematic section
content = content.replace(
    '''            r.so_luong_dang_muon = so_luong_total
            r.so_luong_kha_dung = r.so_luong - so_luong_total
        def action_recalculate_quantity(self):''',
    '''            r.so_luong_dang_muon = so_luong_total
            r.so_luong_kha_dung = r.so_luong - so_luong_total
    
    def action_recalculate_quantity(self):'''
)

# Write
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed indentation!")
