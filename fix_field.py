import re

file_path = r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\tai_san\models\tai_san.py'

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove field declaration (lines 44-50)
pattern1 = r'\s*# Số lượng mượn qua phòng\s*\n\s*so_luong_muon_qua_phong = fields\.Integer\([^)]+\)\s*\n'
content = re.sub(pattern1, '\n', content, flags=re.MULTILINE | re.DOTALL)

# Remove reference in _compute_so_luong_muon (line 226)
pattern2 = r'so_luong_muon = len\(lines\) \+ \(r\.so_luong_muon_qua_phong or 0\)'
content = re.sub(pattern2, '# REMOVED: so_luong_muon_qua_phong reference', content)

# Remove nested method (lines 233-266)
pattern3 = r'\s*@api\.depends\([^\)]+\)\s*\n\s*def _compute_so_luong_muon_qua_phong\(self\):.*?r\.so_luong_muon_qua_phong = total\s*\n'
content = re.sub(pattern3, '\n', content, flags=re.MULTILINE | re.DOTALL)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Field and method references removed successfully!")
