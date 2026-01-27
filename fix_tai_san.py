# -*- coding: utf-8 -*-
"""
Script to fix tai_san.py _compute methods
Run: python fix_tai_san.py
"""

# Code đúng để thay thế từ dòng 221-273
CORRECT_CODE = '''    def _compute_so_luong_muon(self):
        """Tính số lượng đang mượn và khả dụng"""
        PhieuMuonLine = self.env['phieu_muon_tai_san_line']
        for r in self:
            # Đếm số lượng mượn trực tiếp
            lines = PhieuMuonLine.search([
                ('tai_san_id', '=', r.id),
                ('phieu_muon_id.trang_thai', 'in', ['dang_muon', 'qua_han'])
            ])
            so_luong_muon_truc_tiep = sum(lines.mapped('so_luong'))
            
            # Cộng số lượng mượn qua phòng
            so_luong_total = so_luong_muon_truc_tiep + (r.so_luong_muon_qua_phong or 0)
            
            r.so_luong_dang_muon = so_luong_total
            r.so_luong_kha_dung = r.so_luong - so_luong_total
    
    @api.depends('phong_hop_tai_san_ids.phong_hop_id.phieu_muon_ids.trang_thai')
    def _compute_so_luong_muon_qua_phong(self):
        """Tính số lượng tài sản đang mượn qua phòng họp"""
        PhieuMuonPhong = self.env.get('phieu_muon_phong')
        if not PhieuMuonPhong:
            for r in self:
                r.so_luong_muon_qua_phong = 0
            return
        
        for r in self:
            # Tìm phòng có tài sản này  
            phong_tai_san = self.env['phong_hop_tai_san'].search([
                ('tai_san_id', '=', r.id),
                ('loai', '=', 'co_dinh')
            ])
            phong_ids = phong_tai_san.mapped('phong_hop_id').ids
            
            if not phong_ids:
                r.so_luong_muon_qua_phong = 0
                continue
            
            # Tìm phiếu đang mượn
            phieu_active = PhieuMuonPhong.search([
                ('phong_hop_id', 'in', phong_ids),
                ('trang_thai', '=', 'dang_muon')
            ])
            
            # Tính tổng
            total = 0
            for phieu in phieu_active:
                ts_phong = phieu.phong_hop_id.tai_san_ids.filtered(
                    lambda ts: ts.loai == 'co_dinh' and ts.tai_san_id.id == r.id
                )
                total += sum(ts_phong.mapped('so_luong'))
            
            r.so_luong_muon_qua_phong = total
    '''

import codecs
import re

file_path = r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\tai_san\models\tai_san.py'

# Read file
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = f.readlines()

# Find start and end
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if 'def _compute_so_luong_muon(self):' in line and start_idx is None:
        start_idx = i
    if start_idx and 'def action_recalculate_quantity(self):' in line:
        end_idx = i
        break

if start_idx and end_idx:
    print(f"Found: lines {start_idx+1} to {end_idx}")
    
    # Replace
    new_lines = lines[:start_idx] + [CORRECT_CODE + '\n'] + lines[end_idx:]
    
    # Write back
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Fixed!")
else:
    print("❌ Not found")
