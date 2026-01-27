from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import format_datetime
import logging

_logger = logging.getLogger(__name__)


class LichPhongHop(models.Model):
    _name = 'lich_phong_hop'
    _description = 'Lịch phòng họp'
    _rec_name = 'name'
    _order = 'thoi_gian_bat_dau desc'

    # ===== BASIC =====
    name = fields.Char(compute="_compute_name", store=True)

    phong_hop_id = fields.Many2one(
        'phong_hop',
        string="Phòng họp",
        required=True
    )

    nguoi_dat_id = fields.Many2one(
        'nhan_vien',
        string="Người đặt",
        required=True
    )

    thoi_gian_bat_dau = fields.Datetime(string="Bắt đầu", required=True)
    thoi_gian_ket_thuc = fields.Datetime(string="Kết thúc", required=True)

    muc_dich = fields.Text(string="Mục đích")

    # ===== LIÊN KẾT PHIẾU MƯỢN =====
    phieu_muon_id = fields.Many2one(
        'phieu_muon_phong',
        string="Phiếu mượn phòng",
        readonly=True,
        ondelete='set null'
    )

    # ===== DUYỆT =====
    nguoi_duyet_id = fields.Many2one(
        'res.users',
        string="Người duyệt",
        readonly=True,
        ondelete='set null',
        index=True,
        auto_join=False,
    )

    ngay_duyet = fields.Datetime(string="Ngày duyệt", readonly=True)
    ly_do_tu_choi = fields.Text(string="Lý do từ chối")

    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ], default='draft', tracking=True)

    # ===== COMPUTE NAME =====
    @api.depends('phong_hop_id', 'thoi_gian_bat_dau')
    def _compute_name(self):
        for r in self:
            if r.phong_hop_id and r.thoi_gian_bat_dau:
                r.name = "%s | %s" % (
                    r.phong_hop_id.ten_phong,
                    format_datetime(self.env, r.thoi_gian_bat_dau)
                )
            else:
                r.name = "Lịch phòng họp mới"

    # ===== VALIDATION =====
    @api.constrains('thoi_gian_bat_dau', 'thoi_gian_ket_thuc', 'phong_hop_id', 'nguoi_dat_id')
    def _check_time(self):
        for r in self:
            if r.thoi_gian_ket_thuc <= r.thoi_gian_bat_dau:
                raise ValidationError("Thời gian kết thúc phải sau thời gian bắt đầu.")

            if r.phong_hop_id.trang_thai in ['bao_tri', 'ngung']:
                raise ValidationError("Phòng họp đang bảo trì hoặc ngừng hoạt động.")
            
            # Kiểm tra trạng thái nhân viên từ module nhan_su
            if r.nguoi_dat_id and r.nguoi_dat_id.trang_thai != 'dang_lam':
                raise ValidationError("Nhân viên đặt phòng phải đang làm việc. Vui lòng kiểm tra lại trạng thái nhân viên trong module nhân sự.")

            conflict = self.search([
                ('id', '!=', r.id),
                ('phong_hop_id', '=', r.phong_hop_id.id),
                ('trang_thai', 'in', ['cho_duyet', 'approved']),
                ('thoi_gian_bat_dau', '<', r.thoi_gian_ket_thuc),
                ('thoi_gian_ket_thuc', '>', r.thoi_gian_bat_dau),
            ])
            if conflict:
                _logger.warning(
                    "Room booking conflict detected for room %s between %s and %s",
                    r.phong_hop_id.ten_phong,
                    r.thoi_gian_bat_dau,
                    r.thoi_gian_ket_thuc
                )
                raise ValidationError("Phòng họp đã được đặt trong khoảng thời gian này.")

    # ===== WORKFLOW =====
    def action_submit(self):
        self.write({'trang_thai': 'cho_duyet'})

    def action_approve(self):
        """Duyệt lịch phòng họp và tạo phiếu mượn"""
        for r in self:
            if r.phieu_muon_id:
                _logger.info("Lich %s already has phieu_muon, skipping", r.name)
                continue

            # Kiểm tra lại trạng thái nhân viên trước khi duyệt
            if r.nguoi_dat_id.trang_thai != 'dang_lam':
                _logger.error(
                    "Cannot approve: employee %s is not working",
                    r.nguoi_dat_id.ho_va_ten
                )
                raise ValidationError(
                    f"Không thể duyệt. Nhân viên '{r.nguoi_dat_id.ho_va_ten}' không đang làm việc."
                )
            
            # Kiểm tra tài sản phòng họp
            asset_issues = r._check_tai_san_availability()
            if asset_issues:
                _logger.error(
                    "Cannot approve due to asset issues in room %s: %s",
                    r.phong_hop_id.ten_phong, asset_issues
                )
                raise ValidationError(
                    f"Không thể duyệt do các vấn đề về tài sản:\n" + "\n".join(asset_issues)
                )

            # Lấy danh sách tài sản của phòng họp
            tai_san_phong_ids = r.phong_hop_id.tai_san_ids.filtered(lambda ts: ts.tai_san_id)
            
            try:
                # Tạo phiếu mượn phòng với danh sách tài sản
                phieu = self.env['phieu_muon_phong'].create({
                    'phong_hop_id': r.phong_hop_id.id,
                    'nguoi_muon_id': r.nguoi_dat_id.id,
                    'ngay_muon': r.thoi_gian_bat_dau,
                    'ngay_du_kien_tra': r.thoi_gian_ket_thuc,
                    'muc_dich': r.muc_dich,
                    'trang_thai': 'dang_muon',
                    'tai_san_ids': [(6, 0, tai_san_phong_ids.ids)],
                    'lich_phong_hop_id': r.id  # Liên kết 2 chiều
                })

                r.write({
                    'trang_thai': 'approved',
                    'nguoi_duyet_id': self.env.user.id,
                    'ngay_duyet': fields.Datetime.now(),
                    'phieu_muon_id': phieu.id
                })

                # Cập nhật trạng thái phòng
                r.phong_hop_id.trang_thai = 'dang_su_dung'
                
                # Trigger recompute số lượng khả dụng cho các tài sản cố định trong phòng
                if 'tai_san' in self.env:
                    tai_san_ids = tai_san_phong_ids.filtered(lambda ts: ts.la_tai_san_co_dinh).mapped('tai_san_id')
                    if tai_san_ids:
                        tai_san_ids._compute_so_luong_muon()
                        _logger.info(
                            "Recomputed available quantity for %d assets when approving schedule for room '%s'",
                            len(tai_san_ids),
                            r.phong_hop_id.ten_phong
                        )
                
                # Tạo lịch sử với đầy đủ thông tin thời gian
                self.env['lich_su_muon_phong'].create({
                    'phieu_id': phieu.id,
                    'phong_hop_id': r.phong_hop_id.id,
                    'nguoi_muon_id': r.nguoi_dat_id.id,
                    'hanh_dong': 'muon',
                    'tai_san_ids': [(6, 0, tai_san_phong_ids.ids)],
                    'ngay_muon': r.thoi_gian_bat_dau,
                    'ngay_du_kien_tra': r.thoi_gian_ket_thuc,
                    'lich_phong_hop_id': r.id
                })
                
                _logger.info(
                    "Approved lich %s for room %s by %s, created phieu %s",
                    r.name, r.phong_hop_id.ten_phong,
                    r.nguoi_dat_id.ho_va_ten, phieu.name
                )
                
            except Exception as e:
                _logger.error(
                    "Failed to approve lich %s: %s",
                    r.name, str(e)
                )
                raise

    def action_reject(self):
        self.write({
            'trang_thai': 'rejected',
            'nguoi_duyet_id': self.env.user.id,
            'ngay_duyet': fields.Datetime.now()
        })

    def action_cancel(self):
        """Hủy lịch phòng họp"""
        for r in self:
            if r.phieu_muon_id and r.phieu_muon_id.trang_thai == 'dang_muon':
                r.phieu_muon_id.action_tra()
            
            # Đồng bộ trạng thái tài sản khi hủy
            tai_san_phong_ids = r.phong_hop_id.tai_san_ids.filtered(lambda ts: ts.tai_san_id)
            for tai_san_phong in tai_san_phong_ids:
                if tai_san_phong.tai_san_id and tai_san_phong.tai_san_id.trang_thai_su_dung == 'dang_dung':
                    # Kiểm tra xem tài sản có đang được sử dụng ở phòng họp khác không
                    other_meetings = self.search([
                        ('phong_hop_id', '=', r.phong_hop_id.id),
                        ('id', '!=', r.id),
                        ('trang_thai', 'in', ['cho_duyet', 'approved']),
                    ])
                    if not other_meetings:
                        tai_san_phong.tai_san_id.write({
                            'trang_thai_su_dung': 'chua_cap'
                       })
            
            r.trang_thai = 'cancelled'
            
            # Kiểm tra xem còn lịch hoặc phiếu mượn nào đang active không
            other_active_lich = self.search([
                ('phong_hop_id', '=', r.phong_hop_id.id),
                ('id', '!=', r.id),
                ('trang_thai', 'in', ['cho_duyet', 'approved'])
            ])
            
            other_active_phieu = self.env['phieu_muon_phong'].search([
                ('phong_hop_id', '=', r.phong_hop_id.id),
                ('trang_thai', 'in', ['dang_muon', 'qua_han'])
            ])
            
            # Chỉ set về san_sang nếu không còn ai sử dụng
            if not other_active_lich and not other_active_phieu:
                r.phong_hop_id.trang_thai = 'san_sang'
                _logger.info(
                    "Room %s status updated to 'san_sang' (available)",
                    r.phong_hop_id.ten_phong
                )
            
            # Trigger recompute số lượng khả dụng cho các tài sản cố định
            if 'tai_san' in self.env:
                tai_san_ids = tai_san_phong_ids.filtered(lambda ts: ts.la_tai_san_co_dinh).mapped('tai_san_id')
                if tai_san_ids:
                    tai_san_ids._compute_so_luong_muon()
                    _logger.info(
                        "Recomputed available quantity for %d assets after cancelling schedule for room '%s'",
                        len(tai_san_ids),
                        r.phong_hop_id.ten_phong
                    )
            
            _logger.info(
                "Cancelled lich %s for room %s",
                r.name, r.phong_hop_id.ten_phong
            )

    def action_complete(self):
        """Hoàn thành lịch phòng họp"""
        for r in self:
            if r.phieu_muon_id:
                r.phieu_muon_id.action_tra()
            
            # Đồng bộ trạng thái tài sản khi hoàn thành
            tai_san_phong_ids = r.phong_hop_id.tai_san_ids.filtered(lambda ts: ts.tai_san_id)
            for tai_san_phong in tai_san_phong_ids:
                if tai_san_phong.tai_san_id and tai_san_phong.tai_san_id.trang_thai_su_dung == 'dang_dung':
                    # Kiểm tra xem tài sản có đang được sử dụng ở phòng họp khác không
                    other_meetings = self.search([
                        ('phong_hop_id', '=', r.phong_hop_id.id),
                        ('id', '!=', r.id),
                        ('trang_thai', 'in', ['cho_duyet', 'approved']),
                    ])
                    if not other_meetings:
                        tai_san_phong.tai_san_id.write({
                            'trang_thai_su_dung': 'chua_cap'
                        })
            
            r.trang_thai = 'completed'
            
            # Kiểm tra xem còn lịch hoặc phiếu mượn nào đang active không
            other_active_lich = self.search([
                ('phong_hop_id', '=', r.phong_hop_id.id),
                ('id', '!=', r.id),
                ('trang_thai', 'in', ['cho_duyet', 'approved'])
            ])
            
            other_active_phieu = self.env['phieu_muon_phong'].search([
                ('phong_hop_id', '=', r.phong_hop_id.id),
                ('trang_thai', 'in', ['dang_muon', 'qua_han'])
            ])
            
            # Chỉ set về san_sang nếu không còn ai sử dụng
            if not other_active_lich and not other_active_phieu:
                r.phong_hop_id.trang_thai = 'san_sang'
                _logger.info(
                    "Room %s status updated to 'san_sang' (available)",
                    r.phong_hop_id.ten_phong
                )
            
            # Trigger recompute số lượng khả dụng cho các tài sản cố định
            if 'tai_san' in self.env:
                tai_san_ids = tai_san_phong_ids.filtered(lambda ts: ts.la_tai_san_co_dinh).mapped('tai_san_id')
                if tai_san_ids:
                    tai_san_ids._compute_so_luong_muon()
                    _logger.info(
                        "Recomputed available quantity for %d assets after completing schedule for room '%s'",
                        len(tai_san_ids),
                        r.phong_hop_id.ten_phong
                    )
            
            _logger.info(
                "Completed lich %s for room %s",
                r.name, r.phong_hop_id.ten_phong
            )
    
    def _check_tai_san_availability(self):
        """Kiểm tra tài sản phòng họp có sẵn sàng không
        
        Returns:
            list: Danh sách các vấn đề về tài sản (nếu có)
        """
        self.ensure_one()
        issues = []
        
        for tai_san in self.phong_hop_id.tai_san_ids:
            if tai_san.tinh_trang == 'hong':
                issues.append(f"- Tài sản '{tai_san.name}' đang hỏng")
            elif tai_san.tinh_trang == 'mat':
                issues.append(f"- Tài sản '{tai_san.name}' đang mất")
            elif tai_san.tinh_trang == 'sua':
                issues.append(f"- Tài sản '{tai_san.name}' đang sửa chữa")
            
            if tai_san.tai_san_id:
                if tai_san.tai_san_id.trang_thai_su_dung == 'thanh_ly':
                    issues.append(f"- Tài sản '{tai_san.name}' đã được thanh lý")
                elif tai_san.tai_san_id.trang_thai_su_dung == 'hong':
                    issues.append(f"- Tài sản '{tai_san.name}' trong trạng thái hỏng")
        
        return issues
    
    @api.model
    def _cleanup_invalid_foreign_keys(self):
        """
        Cleanup method để fix foreign key constraint violation
        Tự động được gọi khi module được upgrade
        """
        # Set NULL cho các nguoi_duyet_id không tồn tại trong res_users
        invalid_records = self.search([
            ('nguoi_duyet_id', '!=', False)
        ]).filtered(lambda r: not r.nguoi_duyet_id.exists())
        
        if invalid_records:
            invalid_records.write({'nguoi_duyet_id': False})
            return len(invalid_records)
        return 0