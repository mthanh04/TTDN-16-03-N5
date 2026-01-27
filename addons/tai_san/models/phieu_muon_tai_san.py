# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PhieuMuonTaiSan(models.Model):
    _name = 'phieu_muon_tai_san'
    _description = 'Phiếu mượn tài sản'
    _order = 'ngay_muon desc'
    _rec_name = 'name'

    name = fields.Char("Số phiếu", required=True, copy=False, readonly=True, index=True, default='New')
    
    # Hỗ trợ mượn DUY NHẤT 1 tài sản (giữ để tương thích ngược)
    tai_san_id = fields.Many2one('tai_san', string="Tài sản (Deprecated)", help="Chỉ dùng khi mượn 1 tài sản. Nên dùng chi_tiet_ids cho mượn nhiều tài sản")
    
    # MƯỢN NHIỀU TÀI SẢN - TÍNH NĂNG MỚI
    chi_tiet_ids = fields.One2many(
        'phieu_muon_tai_san_line',
        'phieu_muon_id',
        string="Tài sản mượn"
    )
    
    nguoi_muon_id = fields.Many2one('nhan_vien', string="Người mượn", required=True)
    nguoi_duyet_id = fields.Many2one('res.users', string="Người duyệt", readonly=True)
    
    ngay_muon = fields.Datetime("Ngày mượn", default=fields.Datetime.now)
    ngay_tra = fields.Datetime("Ngày trả", readonly=True)
    ngay_du_kien_tra = fields.Datetime("Ngày dự kiến trả", required=True)
    
    muc_dich = fields.Text("Mục đích mượn")
    ly_do_tu_choi = fields.Text("Lý do từ chối")
    ghi_chu = fields.Text("Ghi chú")
    
    # Related field
    nguoi_quan_ly_id = fields.Many2one(
        'nhan_vien',
        related='tai_san_id.nguoi_quan_ly_id',
        string="Người quản lý tài sản",
        store=True,
        readonly=True,
        help="Người quản lý của tài sản có quyền duyệt/từ chối phiếu mượn"
    )
    
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('dang_muon', 'Đang mượn'),
        ('da_tra', 'Đã trả'),
        ('qua_han', 'Quá hạn'),
        ('huy', 'Đã hủy')
    ], default='draft', required=True, tracking=True, string="Trạng thái")
    
    # Computed fields
    duration = fields.Float("Thời gian mượn (giờ)", compute='_compute_duration', store=True)
    is_overdue = fields.Boolean("Quá hạn", compute='_compute_is_overdue')
    
    # Tổng số tài sản mượn
    so_luong_tai_san = fields.Integer("Số tài sản", compute='_compute_so_luong_tai_san', store=True)
    
    @api.depends('chi_tiet_ids', 'tai_san_id')
    def _compute_so_luong_tai_san(self):
        """Tính số tài sản mượn"""
        for record in self:
            if record.chi_tiet_ids:
                record.so_luong_tai_san = len(record.chi_tiet_ids)
            elif record.tai_san_id:
                record.so_luong_tai_san = 1
            else:
                record.so_luong_tai_san = 0
    
    @api.depends('ngay_muon', 'ngay_tra', 'ngay_du_kien_tra')
    def _compute_duration(self):
        """Tính thời gian mượn"""
        for record in self:
            if record.ngay_muon:
                end_date = record.ngay_tra or record.ngay_du_kien_tra or fields.Datetime.now()
                delta = end_date - record.ngay_muon
                record.duration = delta.total_seconds() / 3600.0
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
            vals['name'] = self.env['ir.sequence'].next_by_code('phieu_muon_tai_san') or 'New'
        return super().create(vals)
    
    @api.constrains('nguoi_muon_id')
    def _check_nguoi_muon(self):
        """Kiểm tra trạng thái nhân viên"""
        for record in self:
            if record.nguoi_muon_id and record.nguoi_muon_id.trang_thai != 'dang_lam':
                raise ValidationError(
                    f"Nhân viên '{record.nguoi_muon_id.ho_va_ten}' không đang làm việc."
                )
    
    @api.constrains('ngay_muon', 'ngay_du_kien_tra')
    def _check_ngay(self):
        """Kiểm tra ngày dự kiến trả phải sau ngày mượn"""
        for record in self:
            if record.ngay_du_kien_tra and record.ngay_muon:
                if record.ngay_du_kien_tra <= record.ngay_muon:
                    raise ValidationError("Ngày dự kiến trả phải sau ngày mượn")
    
    def action_submit(self):
        """Gửi duyệt"""
        self.write({'trang_thai': 'cho_duyet'})
    
    def action_approve(self):
        """Duyệt và cho mượn - Hỗ trợ cả mượn 1 tài sản và nhiều tài sản"""
        for r in self:
            current_user = self.env.user
            
            # Xác định danh sách tài sản mượn
            if r.chi_tiet_ids:
                # MƯỢN NHIỀU TÀI SẢN (tính năng mới)
                tai_sans = r.chi_tiet_ids.mapped('tai_san_id')
            elif r.tai_san_id:
                # MƯỢN 1 TÀI SẢN (tương thích ngược)
                tai_sans = r.tai_san_id
            else:
                raise ValidationError("Phiếu mượn phải có ít nhất 1 tài sản!")
            
            # VALIDATION: Kiểm tra từng tài sản
            for ts in tai_sans:
                # 1. Tài sản phải có người quản lý
                if not ts.nguoi_quan_ly_id:
                    raise ValidationError(
                        f"Tài sản '{ts.ten_tai_san}' chưa được cấp phát cho người quản lý nào. "
                        "Không thể mượn. Vui lòng tạo phiếu cấp phát trước."
                    )
                
                # 2. Chỉ người quản lý mới duyệt được
                manager = ts.nguoi_quan_ly_id
                if manager.user_id:
                    if current_user != manager.user_id and not self.user_has_groups('tai_san.group_asset_manager'):
                        raise ValidationError(
                            f"Chỉ người quản lý '{manager.ho_va_ten}' "
                           f"mới có quyền duyệt phiếu mượn tài sản '{ts.ten_tai_san}'."
                        )
                else:
                    # Manager không có user, chỉ admin duyệt được
                    if not self.user_has_groups('tai_san.group_asset_manager'):
                        raise ValidationError(
                            f"Người quản lý '{manager.ho_va_ten}' chưa liên kết với tài khoản hệ thống. "
                            "Chỉ quản trị viên mới có thể duyệt."
                        )
                
                # 3. Tài sản phải sẵn sàng để mượn
                if ts.trang_thai_su_dung == 'dang_muon':
                    raise ValidationError(
                        f"Tài sản '{ts.ten_tai_san}' đang được mượn bởi "
                        f"'{ts.nguoi_muon_id.ho_va_ten}'. "
                        "Vui lòng chọn tài sản khác."
                    )
                
                if ts.trang_thai_su_dung != 'da_cap_phat':
                    raise ValidationError(
                        f"Tài sản '{ts.ten_tai_san}' không thể mượn do "
                        f"trạng thái: {dict(ts._fields['trang_thai_su_dung'].selection).get(ts.trang_thai_su_dung)}"
                    )
            
            # CẬP NHẬT trạng thái từng tài sản
            for ts in tai_sans:
                ts.write({
                    'trang_thai_su_dung': 'dang_muon',
                    'nguoi_muon_id': r.nguoi_muon_id.id,
                    'ngay_muon': r.ngay_muon,
                    'ngay_du_kien_tra': r.ngay_du_kien_tra
                })
                
                # Tạo lịch sử: Mượn
                self.env['tai_san_lich_su'].create({
                    'tai_san_id': ts.id,
                    'phieu_muon_id': r.id,
                    'hanh_dong': 'muon',
                    'nguoi_muon_id': r.nguoi_muon_id.id,
                    'ngay_muon': r.ngay_muon,
                    'ngay_du_kien_tra': r.ngay_du_kien_tra,
                    'ghi_chu': r.muc_dich
                })
            
            r.write({
                'trang_thai': 'dang_muon',
                'nguoi_duyet_id': current_user.id
            })
            
            # CẬP NHẬT số lượng khả dụng của tất cả tài sản
            tai_sans._compute_so_luong_muon()
            
            _logger.info(
                "Approved borrow request %s: %s borrows %d asset(s)",
                r.name,
                r.nguoi_muon_id.ho_va_ten,
                len(tai_sans)
            )
    
    
    def action_reject(self):
        """Từ chối phiếu mượn - Chỉ người quản lý tài sản mới từ chối được"""
        for r in self:
            # Validation: Chỉ người quản lý mới từ chối được
            current_user = self.env.user
            manager = r.tai_san_id.nguoi_quan_ly_id
            
            if manager and manager.user_id:
                if current_user != manager.user_id:
                    raise ValidationError(
                        f"Chỉ người quản lý '{manager.ho_va_ten}' "
                        f"mới có quyền từ chối phiếu mượn."
                    )
            
            r.write({
                'trang_thai': 'huy',
                'nguoi_duyet_id': current_user.id
            })
            
            _logger.info(
                "Manager %s rejected borrow request %s (reason: %s)",
                manager.ho_va_ten if manager else 'Admin',
                r.name,
                r.ly_do_tu_choi or 'No reason provided'
            )
    
    def action_tra(self):
        """Trả tài sản - Hỗ trợ cả trả 1 tài sản và nhiều tài sản"""
        for r in self:
            r.ngay_tra = fields.Datetime.now()
            
            # Xác định danh sách tài sản cần trả
            if r.chi_tiet_ids:
                tai_sans = r.chi_tiet_ids.mapped('tai_san_id')
            elif r.tai_san_id:
                tai_sans = r.tai_san_id
            else:
                tai_sans = self.env['tai_san']
            
            # Trả từng tài sản về lại người quản lý
            for ts in tai_sans:
                new_status = 'da_cap_phat' if ts.nguoi_quan_ly_id else 'chua_cap'
                
                ts.write({
                    'trang_thai_su_dung': new_status,
                    'nguoi_muon_id': False,
                    'ngay_muon': False,
                    'ngay_du_kien_tra': False
                })
                
                # Tạo lịch sử: Trả
                self.env['tai_san_lich_su'].create({
                    'tai_san_id': ts.id,
                    'phieu_muon_id': r.id,
                    'hanh_dong': 'tra',
                    'nguoi_muon_id': r.nguoi_muon_id.id,
                    'ngay_muon': r.ngay_muon,
                    'ngay_tra': r.ngay_tra,
                    'ngay_du_kien_tra': r.ngay_du_kien_tra
                })
            
            r.trang_thai = 'da_tra'
            
            # CẬP NHẬT số lượng khả dụng của tất cả tài sản
            tai_sans._compute_so_luong_muon()
            
            _logger.info(
                "%d asset(s) returned by %s (phieu: %s)",
                len(tai_sans),
                r.nguoi_muon_id.ho_va_ten,
                r.name
            )
    
    
    
    def action_cancel(self):
        """Hủy phiếu mượn"""
        for r in self:
            if r.trang_thai == 'dang_muon':
                raise ValidationError("Không thể hủy phiếu đang mượn. Vui lòng trả tài sản trước.")
            r.trang_thai = 'huy'
    
    @api.model
    def action_check_qua_han(self):
        """Scheduled action để check phiếu quá hạn và tự động thu hồi tài sản"""
        overdue_phieus = self.search([
            ('trang_thai', '=', 'dang_muon'),
            ('ngay_du_kien_tra', '<', fields.Datetime.now())
        ])
        
        for phieu in overdue_phieus:
            # Log warning trước khi thu hồi
            _logger.warning(
                "Phieu %s is overdue. Borrower: %s. Auto-returning assets...",
                phieu.name, phieu.nguoi_muon_id.ho_va_ten
            )
            
            # Tự động trả tài sản (gọi action_tra)
            # action_tra() sẽ:
            # - Reset tài sản về người quản lý
            # - Tạo lịch sử trả
            # - Set trang_thai = 'da_tra'
            phieu.action_tra()
            
            # Override trạng thái về 'qua_han' để phân biệt với trả bình thường
            phieu.write({'trang_thai': 'qua_han'})
            
            # Thêm ghi chú vào lịch sử để đánh dấu là auto-return
            # Tìm lịch sử vừa tạo (lịch sử trả gần nhất)
            recent_histories = self.env['tai_san_lich_su'].search([
                ('phieu_muon_id', '=', phieu.id),
                ('hanh_dong', '=', 'tra'),
            ], order='ngay desc, id desc')
            
            if recent_histories:
                # Lấy tài sản từ phiếu
                if phieu.chi_tiet_ids:
                    tai_sans = phieu.chi_tiet_ids.mapped('tai_san_id')
                elif phieu.tai_san_id:
                    tai_sans = [phieu.tai_san_id]
                else:
                    tai_sans = []
                
                # Update ghi chú cho các lịch sử của tài sản trong phiếu này
                for ts in tai_sans:
                    ts_history = recent_histories.filtered(lambda h: h.tai_san_id == ts)
                    if ts_history:
                        ts_history[0].write({
                            'ghi_chu': 'Tự động thu hồi do quá hạn trả (Auto-returned due to overdue)'
                        })
            
            _logger.info(
                "Auto-returned assets for overdue phieu %s. Borrower: %s",
                phieu.name, phieu.nguoi_muon_id.ho_va_ten
            )
        
        if overdue_phieus:
            _logger.info(
                "Checked and auto-returned %d overdue phieus", 
                len(overdue_phieus)
            )
        
        return True
