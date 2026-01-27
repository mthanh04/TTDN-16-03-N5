# Fix corrupted quote and set maxOutputTokens to 2048
with open(r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\phong_hop\wizard\phong_hop_ai_suggest.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the corrupted escape sequence
content = content.replace('"maxOutputTokens\\x22:', '"maxOutputTokens":')

# Write back
with open(r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\phong_hop\wizard\phong_hop_ai_suggest.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed quote character successfully")
