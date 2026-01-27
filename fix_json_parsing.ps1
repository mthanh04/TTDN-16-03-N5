$file = "d:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\phong_hop\wizard\phong_hop_ai_suggest.py"
$content = Get-Content $file -Raw

# Fix parsing by adding try-catch
$content = $content -replace 'data = json\.loads\(ai_text\)', @'
try:
            data = json.loads(ai_text)
        except json.JSONDecodeError as e:
            _logger.error("AI returned invalid JSON: %s", ai_text)
            raise Exception(f"AI trả JSON không hợp lệ: {e}")
'@

$content | Set-Content $file
Write-Host "Fixed JSON parsing error handling"
