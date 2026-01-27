# Fix line 118 - replace corrupted quote with proper quote
with open(r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\phong_hop\wizard\phong_hop_ai_suggest.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 118 (index 117)
lines[117] = '                "maxOutputTokens": 2048\r\n'

with open(r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\phong_hop\wizard\phong_hop_ai_suggest.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed line 118 successfully!")
