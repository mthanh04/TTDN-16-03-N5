#!/usr/bin/env python3
# Add room asset counting to tai_san.py

file_path = r'd:\TTCNTT7\Odoo_code\TTDN-16-03-N5\addons\tai_san\models\tai_san.py'

# New helper method
HELPER_METHOD = '''    
    def _get_so_luong_muon_qua_phong(self):
        """Helper: Tính số lượng tài sản đang mượn qua phòng họp"""
        self.ensure_one()
        
        # Kiểm tra module phong_hop có không
        if 'phieu_muon_phong' not in self.env:
            return 0
        
        PhieuMuonPhong = self.env['phieu_muon_phong']
        PhongHopTaiSan = self.env['phong_hop_tai_san']
        
        # Tìm tất cả phòng có tài sản này (cố định)
        phong_co_tai_san = PhongHopTaiSan.search([
            ('tai_san_id', '=', self.id),
            ('loai', '=', 'co_dinh')
        ])
        
        if not phong_co_tai_san:
            return 0
        
        phong_ids = phong_co_tai_san.mapped('phong_hop_id').ids
        
        # Tìm phiếu mượn phòng đang active
        phieu_active = PhieuMuonPhong.search([
            ('phong_hop_id', 'in', phong_ids),
            ('trang_thai', '=', 'dang_muon')
        ])
        
        # Tính tổng số lượng
        total = 0
        for phieu in phieu_active:
            # Lấy tài sản cố định trong phòng này
            ts_trong_phong = phieu.phong_hop_id.tai_san_ids.filtered(
                lambda ts: ts.loai == 'co_dinh' and ts.tai_san_id.id == self.id
            )
            total += sum(ts_trong_phong.mapped('so_luong'))
        
        return total
    
'''

# Updated compute method
COMPUTE_METHOD = '''    def _compute_so_luong_muon(self):
        """Tính số lượng đang mượn và khả dụng"""
        PhieuMuonLine = self.env['phieu_muon_tai_san_line']
        for r in self:
            # Đếm số lượng trong các phiếu mượn đang active
            lines = PhieuMuonLine.search([
                ('tai_san_id', '=', r.id),
                ('phieu_muon_id.trang_thai', 'in', ['dang_muon', 'qua_han'])
            ])
            
            # Số lượng mượn trực tiếp
            so_luong_muon_truc_tiep = sum(lines.mapped('so_luong'))
            
            # Cộng số lượng mượn qua phòng
            so_luong_muon_qua_phong = r._get_so_luong_muon_qua_phong()
            
            # Tổng
            so_luong_total = so_luong_muon_truc_tiep + so_luong_muon_qua_phong
            
            r.so_luong_dang_muon = so_luong_total
            r.so_luong_kha_dung = r.so_luong - so_luong_total
    '''

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line with def _compute_so_luong_muon
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if 'def _compute_so_luong_muon(self):' in line and start_idx is None:
        start_idx = i
    if start_idx and i > start_idx and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
        end_idx = i
        break
    if start_idx and 'def action_recalculate_quantity(self):' in line:
        end_idx = i
        break

if start_idx and end_idx:
    # Insert helper method before _compute_so_luong_muon
    # Replace _compute_so_luong_muon
    new_lines = lines[:start_idx] + [HELPER_METHOD, COMPUTE_METHOD] + lines[end_idx:]
    
    # Write
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"SUCCESS: Added helper method and updated _compute_so_luong_muon (lines {start_idx+1}-{end_idx})")
else:
    print("ERROR: Could not find target method")
