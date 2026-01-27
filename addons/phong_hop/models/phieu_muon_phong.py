from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PhieuMuonPhong(models.Model):
    _name = 'phieu_muon_phong'
    _description = 'Phiếu mượn phòng'
    _rec_name = 'name'

    name = fields.Char("Số phiếu", required=True, copy=False, readonly=True, index=True, default='New')
    phong_hop_id = fields.Many2one('phong_hop', string="Phòng họp", required=True)
    nguoi_muon_id = fields.Many2one('nhan_vien', string="Người mượn", required=True)

    ngay_muon = fields.Datetime("Ngày mượn", default=fields.Datetime.now, required=True)
    ngay_tra = fields.Datetime("Ngày trả")
    ngay_du_kien_tra = fields.Datetime("Ngày dự kiến trả")

    muc_dich = fields.Text("Mục đích")

    # Liên kết với lịch phòng họp
    lich_phong_hop_id = fields.Many2one(
        'lich_phong_hop',
        string="Lịch phòng họp",
        readonly=True,
        ondelete='set null',
        help="Lịch phòng họp tương ứng (tự động tạo nếu chưa có)"
    )

    tai_san_ids = fields.Many2many('phong_hop_tai_san', string="Tài sản sử dụng")

    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('dang_muon', 'Đang mượn'),
        ('da_tra', 'Đã trả'),
        ('qua_han', 'Quá hạn')
    ], default='draft', string="Trạng thái", tracking=True)
    
    # Asset warning fields
    asset_warning = fields.Text(
        "Cảnh báo tài sản",
        compute='_compute_asset_warning',
        store=False,
        help="Danh sách tài sản có vấn đề"
    )
    
    ignore_asset_warning = fields.Boolean(
        "Tôi đã biết và vẫn muốn mượn phòng",
        default=False,
        help="Tick vào đây nếu bạn vẫn muốn mượn phòng dù có tài sản hỏng/sửa"
    )
    
    # Computed fields
    duration = fields.Float("Thời gian sử dụng (giờ)", compute='_compute_duration', store=True)
    is_overdue = fields.Boolean("Quá hạn", compute='_compute_is_overdue')
    
    
    @api.depends('phong_hop_id', 'phong_hop_id.tai_san_ids', 'phong_hop_id.tai_san_ids.tinh_trang')
    def _compute_asset_warning(self):
        """Ấnh toán cảnh báo tài sản"""
        for r in self:
            problems = []
            for ts in r.phong_hop_id.tai_san_ids:
                if ts.tinh_trang in ['hong', 'sua']:
                    status = dict(ts._fields['tinh_trang'].selection).get(ts.tinh_trang)
                    problems.append(f"• {ts.name}: {status}")
            
            r.asset_warning = "\n".join(problems) if problems else False
    
    @api.onchange('phong_hop_id')
    def _onchange_phong_hop_id(self):
        """Tự động điền danh sách tài sản cố định của phòng"""
        if self.phong_hop_id:
            # Lấy tất cả tài sản cố định của phòng
            tai_san_co_dinh = self.phong_hop_id.tai_san_ids.filtered(
                lambda ts: ts.la_tai_san_co_dinh and ts.tinh_trang not in ['hong', 'mat']
            )
            self.tai_san_ids = [(6, 0, tai_san_co_dinh.ids)]
            _logger.info(
                "Auto-populated %d permanent assets for room '%s'",
                len(tai_san_co_dinh),
                self.phong_hop_id.ten_phong
            )
    
    @api.depends('ngay_muon', 'ngay_tra', 'ngay_du_kien_tra')
    def _compute_duration(self):
        """Tính thời gian sử dụng"""
        for record in self:
            if record.ngay_muon:
                end_date = record.ngay_tra or record.ngay_du_kien_tra or fields.Datetime.now()
                delta = end_date - record.ngay_muon
                record.duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                record.duration = 0.0
    
    @api.depends('ngay_du_kien_tra', 'trang_thai')
    def _compute_is_overdue(self):
        """Kiểm tra có quá hạn không"""
        for record in self:
            if record.trang_thai == 'dang_muon' and record.ngay_du_kien_tra:
                record.is_overdue = fields.Datetime.now() > record.ngay_du_kien_tra
            else:
                record.is_overdue = False
    
    @api.model
    def create(self, vals):
        """Tự động tạo số phiếu"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('phieu_muon_phong') or 'New'
        result = super().create(vals)
        _logger.info("Created phieu muon phong: %s for room %s", result.name, result.phong_hop_id.ten_phong)
        return result
    
    @api.constrains('nguoi_muon_id')
    def _check_nguoi_muon(self):
        """Kiểm tra trạng thái nhân viên từ module nhan_su"""
        for record in self:
            if record.nguoi_muon_id and record.nguoi_muon_id.trang_thai != 'dang_lam':
                raise ValidationError(
                    f"Nhân viên '{record.nguoi_muon_id.ho_va_ten}' không đang làm việc. "
                    "Vui lòng kiểm tra lại trạng thái nhân viên trong module nhân sự."
                )
    
    @api.constrains('ngay_muon', 'ngay_du_kien_tra')
    def _check_ngay(self):
        """Kiểm tra ngày dự kiến trả phải sau ngày mượn"""
        for record in self:
            if record.ngay_du_kien_tra and record.ngay_muon:
                if record.ngay_du_kien_tra <= record.ngay_muon:
                    raise ValidationError("Ngày dự kiến trả phải sau ngày mượn")

    def action_muon(self):
        """Thực hiện mượn phòng"""
        for r in self:
            # Kiểm tra lại trạng thái nhân viên
            if r.nguoi_muon_id.trang_thai != 'dang_lam':
                _logger.error("Cannot borrow room: employee %s is not working", r.nguoi_muon_id.ho_va_ten)
                raise ValidationError(f"Không thể mượn phòng. Nhân viên '{r.nguoi_muon_id.ho_va_ten}' không đang làm việc.")
            
            # Kiểm tra tài sản phòng họp
            problem_assets = []
            missing_assets = []
            
            for tai_san in r.phong_hop_id.tai_san_ids:
                # Chặn hoàn toàn nếu tài sản bị mất
                if tai_san.tinh_trang == 'mat':
                    missing_assets.append(tai_san.name)
                # Thu thập tài sản hỏng/sửa để cảnh báo
                elif tai_san.tinh_trang in ['hong', 'sua']:
                    status = dict(tai_san._fields['tinh_trang'].selection).get(tai_san.tinh_trang)
                    problem_assets.append(f"  • {tai_san.name}: {status}")
            
            # Chặn hoàn toàn nếu có tài sản mất
            if missing_assets:
                asset_list = ", ".join(missing_assets)
                _logger.error(
                    "Cannot borrow room %s: missing assets %s",
                    r.phong_hop_id.ten_phong, asset_list
                )
                raise ValidationError(
                    f"❌ Không thể mượn phòng!\\n\\n"
                    f"Các tài sản sau đã bị mất: {asset_list}\\n\\n"
                    f"Vui lòng liên hệ quản trị viên để cập nhật trạng thái phòng."
                )
            
            # Cảnh báo và yêu cầu xác nhận nếu có tài sản hỏng/sửa
            if problem_assets and not r.ignore_asset_warning:
                warning_text = "\\n".join(problem_assets)
                _logger.warning(
                    "Room %s has problematic assets, user needs to confirm",
                    r.phong_hop_id.ten_phong
                )
                raise ValidationError(
                    f"⚠️ Cảnh báo: Có tài sản trong phòng đang có vấn đề:\\n\\n{warning_text}\\n\\n"
                    f"Nếu bạn vẫn muốn mượn phòng, vui lòng tick vào ô \\n"
                    f"'✅ Tôi đã biết và vẫn muốn mượn phòng' ở dưới và thử lại."
                )
            
            # Nếu đã confirm, log cảnh báo và tiếp tục
            if problem_assets and r.ignore_asset_warning:
                _logger.warning(
                    "User %s confirmed to borrow room %s despite asset issues",
                    r.nguoi_muon_id.ho_va_ten, r.phong_hop_id.ten_phong
                )
            
            # Kiểm tra phòng có bị trùng lịch không
            overlap = self.search([
                ('id', '!=', r.id),
                ('phong_hop_id', '=', r.phong_hop_id.id),
                ('trang_thai', '=', 'dang_muon')
            ])
            if overlap:
                raise ValidationError(
                    f"Phòng '{r.phong_hop_id.ten_phong}' đang được mượn bởi '{overlap[0].nguoi_muon_id.ho_va_ten}'. "
                    "Vui lòng chọn phòng khác hoặc đợi phòng được trả."
                )
            
            # Cập nhật trạng thái
            r.trang_thai = 'dang_muon'
            r.ngay_muon = fields.Datetime.now()
            
            # Nếu chưa có tài sản, tự động lấy tài sản cố định của phòng
            if not r.tai_san_ids:
                tai_san_co_dinh = r.phong_hop_id.tai_san_ids.filtered(
                    lambda ts: ts.la_tai_san_co_dinh and ts.tinh_trang not in ['hong', 'mat']
                )
                r.tai_san_ids = [(6, 0, tai_san_co_dinh.ids)]
                _logger.info(
                    "Auto-added %d permanent assets to borrow request for room '%s'",
                    len(tai_san_co_dinh),
                    r.phong_hop_id.ten_phong
                )
            
            # Nếu chưa có lịch phòng họp, tự động tạo
            if not r.lich_phong_hop_id:
                try:
                    lich = self.env['lich_phong_hop'].create({
                        'phong_hop_id': r.phong_hop_id.id,
                        'nguoi_dat_id': r.nguoi_muon_id.id,
                        'thoi_gian_bat_dau': r.ngay_muon,
                        'thoi_gian_ket_thuc': r.ngay_du_kien_tra or r.ngay_muon,
                        'muc_dich': r.muc_dich,
                        'trang_thai': 'approved',  # Đã duyệt luôn vì đang mượn
                        'nguoi_duyet_id': self.env.user.id,
                        'ngay_duyet': fields.Datetime.now(),
                        'phieu_muon_id': r.id
                    })
                    r.lich_phong_hop_id = lich.id
                    _logger.info(
                        "Auto-created lich_phong_hop %s for phieu %s",
                        lich.name, r.name
                    )
                except Exception as e:
                    _logger.error(
                        "Failed to create lich_phong_hop for phieu %s: %s",
                        r.name, str(e)
                    )
                    # Tiếp tục mượn phòng nhưng không có lịch
            
            # Tạo lịch sử với đầy đủ thông tin thời gian
            self.env['lich_su_muon_phong'].create({
                'phieu_id': r.id,
                'phong_hop_id': r.phong_hop_id.id,
                'nguoi_muon_id': r.nguoi_muon_id.id,
                'hanh_dong': 'muon',
                'tai_san_ids': [(6, 0, r.tai_san_ids.ids)],
                'ngay_muon': r.ngay_muon,
                'ngay_du_kien_tra': r.ngay_du_kien_tra,
                'lich_phong_hop_id': r.lich_phong_hop_id.id if r.lich_phong_hop_id else False
            })
            
            # Cập nhật trạng thái phòng họp thành đang sử dụng
            r.phong_hop_id.trang_thai = 'dang_su_dung'
            
            # Trigger recompute số lượng khả dụng cho các tài sản cố định trong phòng
            if 'tai_san' in self.env:
                tai_san_ids = r.tai_san_ids.filtered(lambda ts: ts.la_tai_san_co_dinh).mapped('tai_san_id')
                if tai_san_ids:
                    tai_san_ids._compute_so_luong_muon()
                    _logger.info(
                        "Recomputed available quantity for %d assets in room '%s'",
                        len(tai_san_ids),
                        r.phong_hop_id.ten_phong
                    )
            
            _logger.info(
                "Room %s borrowed by %s (phieu: %s)",
                r.phong_hop_id.ten_phong, r.nguoi_muon_id.ho_va_ten, r.name
            )

    def action_tra(self):
        """Trả phòng"""
        for r in self:
            r.trang_thai = 'da_tra'
            r.ngay_tra = fields.Datetime.now()
            
            # Cập nhật lịch phòng họp nếu có
            if r.lich_phong_hop_id and r.lich_phong_hop_id.trang_thai == 'approved':
                try:
                    r.lich_phong_hop_id.write({'trang_thai': 'completed'})
                    _logger.info(
                        "Updated lich_phong_hop %s to completed",
                        r.lich_phong_hop_id.name
                    )
                except Exception as e:
                    _logger.error(
                        "Failed to update lich_phong_hop: %s", str(e)
                    )
            
            # Tạo lịch sử với thời gian trả
            self.env['lich_su_muon_phong'].create({
                'phieu_id': r.id,
                'phong_hop_id': r.phong_hop_id.id,
                'nguoi_muon_id': r.nguoi_muon_id.id,
                'hanh_dong': 'tra',
                'tai_san_ids': [(6, 0, r.tai_san_ids.ids)],
                'ngay_muon': r.ngay_muon,
                'ngay_tra': r.ngay_tra,
                'lich_phong_hop_id': r.lich_phong_hop_id.id if r.lich_phong_hop_id else False
            })
            
            # Đồng bộ trạng thái tài sản với module tai_san khi trả
            for tai_san_phong in r.tai_san_ids:
                if tai_san_phong.tai_san_id:
                    # Kiểm tra xem tài sản có đang được sử dụng ở phiếu mượn khác không
                    other_phieu = self.search([
                        ('phong_hop_id', '=', r.phong_hop_id.id),
                        ('id', '!=', r.id),
                        ('trang_thai', '=', 'dang_muon'),
                        ('tai_san_ids', 'in', [tai_san_phong.id])
                    ])
                    
                    # Chỉ reset về 'chua_cap' nếu không còn ai sử dụng
                    if not other_phieu:
                        # Kiểm tra xem có lịch phòng họp nào đang sử dụng không
                        lich_phong_hop = self.env['lich_phong_hop'].search([
                            ('phong_hop_id', '=', r.phong_hop_id.id),
                            ('trang_thai', 'in', ['cho_duyet', 'approved']),
                        ])
                        
                        if not lich_phong_hop:
                            # Nếu là tài sản cố định, giữ trạng thái 'chua_cap' nhưng vẫn thuộc phòng
                            # Nếu không phải tài sản cố định, reset về chưa cấp
                            tai_san_phong.tai_san_id.write({
                                'trang_thai_su_dung': 'chua_cap'
                            })
                            _logger.info(
                                "Asset %s reset to unassigned status (Permanent: %s)",
                                tai_san_phong.tai_san_id.ten_tai_san,
                                tai_san_phong.la_tai_san_co_dinh
                            )
            
            # Cập nhật trạng thái phòng họp về sẵn sàng
            # Kiểm tra xem còn phiếu mượn nào đang sử dụng phòng này không
            other_active_phieu = self.search([
                ('phong_hop_id', '=', r.phong_hop_id.id),
                ('id', '!=', r.id),
                ('trang_thai', 'in', ['dang_muon', 'qua_han'])
            ])
            
            # Kiểm tra xem còn lịch phòng họp nào đang active không
            active_lich = self.env['lich_phong_hop'].search([
                ('phong_hop_id', '=', r.phong_hop_id.id),
                ('trang_thai', 'in', ['cho_duyet', 'approved'])
            ])
            
            # Chỉ set phòng về 'san_sang' nếu không còn ai sử dụng
            if not other_active_phieu and not active_lich:
                r.phong_hop_id.trang_thai = 'san_sang'
                _logger.info(
                    "Room %s status updated to 'san_sang' (available)",
                    r.phong_hop_id.ten_phong
                )
            else:
                _logger.info(
                    "Room %s still in use by other bookings/borrow slips",
                    r.phong_hop_id.ten_phong
                )
            
            # Trigger recompute số lượng khả dụng cho các tài sản cố định trong phòng
            if 'tai_san' in self.env:
                tai_san_ids = r.tai_san_ids.filtered(lambda ts: ts.la_tai_san_co_dinh).mapped('tai_san_id')
                if tai_san_ids:
                    tai_san_ids._compute_so_luong_muon()
                    _logger.info(
                        "Recomputed available quantity for %d assets after returning room '%s'",
                        len(tai_san_ids),
                        r.phong_hop_id.ten_phong
                    )
            
            _logger.info(
                "Room %s returned by %s (phieu: %s)",
                r.phong_hop_id.ten_phong, r.nguoi_muon_id.ho_va_ten, r.name
            )
    
    @api.model
    def action_check_qua_han(self):
        """Scheduled action để check phiếu quá hạn"""
        overdue_phieus = self.search([
            ('trang_thai', '=', 'dang_muon'),
            ('ngay_du_kien_tra', '<', fields.Datetime.now())
        ])
        
        for phieu in overdue_phieus:
            phieu.write({'trang_thai': 'qua_han'})
            
            # Tạo lịch sử
            self.env['lich_su_muon_phong'].create({
                'phieu_id': phieu.id,
                'phong_hop_id': phieu.phong_hop_id.id,
                'nguoi_muon_id': phieu.nguoi_muon_id.id,
                'hanh_dong': 'qua_han',
                'ghi_chu': 'Tự động đánh dấu quá hạn bởi hệ thống'
            })
            
            _logger.warning(
                "Phieu %s is overdue. Room: %s, Borrower: %s",
                phieu.name, phieu.phong_hop_id.ten_phong, phieu.nguoi_muon_id.ho_va_ten
            )
        
        if overdue_phieus:
            _logger.info("Checked and marked %d overdue phieus", len(overdue_phieus))
        
        return True