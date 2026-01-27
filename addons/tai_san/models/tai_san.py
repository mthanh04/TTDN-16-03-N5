# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TaiSan(models.Model):
    _name = 'tai_san'
    _description = 'Tài sản'
    _rec_name = 'ten_tai_san'
    _order = 'ma_tai_san asc'

    ma_tai_san = fields.Char("Mã tài sản", required=True, index=True, copy=False, default='New')
    so_serial = fields.Char("Số Serial", help="Số serial của thiết bị (nếu có)")
    ten_tai_san = fields.Char("Tên tài sản", required=True)
    
    loai_tai_san_id = fields.Many2one(
        'loai_tai_san',
        string="Loại tài sản",
        required=True
    )
    
    # === SỐ LƯỢNG & TÀI CHÍNH ===
    so_luong = fields.Integer("Số lượng", default=1, required=True, help="Tổng số lượng tài sản")
    
    # Số lượng đang mượn
    so_luong_dang_muon = fields.Integer(
        "Số lượng đang mượn",
        compute='_compute_so_luong_muon',
        store=True,
        default=0,
        help="Số lượng tài sản đang được mượn"
    )
    
    # Số lượng khả dụng
    so_luong_kha_dung = fields.Integer(
        "Số lượng khả dụng",
        compute='_compute_so_luong_muon',
        store=True,
        default=0,
        help="Số lượng tài sản có thể mượn = Tổng - Đang mượn"
    )
    gia_mua = fields.Float("Giá mua (đơn vị)", digits=(16, 0), default=0, help="Giá mua của mỗi đơn vị tài sản")
    gia_hien_tai = fields.Float(
        "Giá hiện tại (đơn vị)",
        compute='_compute_gia_hien_tai',
        store=True,
        digits=(16, 0),
        help="Giá hiện tại sau khi trừ khấu hao"
    )
    
    # Tổng (computed)
    tong_gia_mua = fields.Float(
        "Tổng giá mua",
        compute='_compute_tong',
        store=True,
        digits=(16, 0)
    )
    tong_khau_hao = fields.Float(
        "Tổng khấu hao",
        compute='_compute_tong',
        store=True,
        digits=(16, 0)
    )
    tong_gia_hien_tai = fields.Float(
        "Tổng giá hiện tại",
        compute='_compute_tong',
        store=True,
        digits=(16, 0)
    )
    
    # === NHÀ CUNG CẤP ===
    nha_cung_cap_id = fields.Many2one(
        'nha_cung_cap',
        string="Nhà cung cấp"
    )
    
    ngay_mua = fields.Date("Ngày mua")
    
    # === KHẤU HAO ===
    thoi_gian_su_dung_du_kien = fields.Integer(
        "Thời gian sử dụng dự kiến (năm)",
        default=5,
        help="Thời gian sử dụng dự kiến của tài sản"
    )
    phuong_phap_khau_hao = fields.Selection([
        ('duong_thang', 'Đường thẳng'),
        ('so_du_giam_dan', 'Số dư giảm dần')
    ], string="Phương pháp khấu hao", default='duong_thang')
    ty_le_khau_hao = fields.Float(
        "Tỷ lệ khấu hao (%/năm)",
        compute='_compute_ty_le_khau_hao',
        store=True
    )
    
    tinh_trang = fields.Selection(
        [
            ('moi', 'Mới'),
            ('cu', 'Cũ'),
            ('hong', 'Hỏng')
        ],
        string="Tình trạng",
        default='moi',
        required=True
    )
    
    trang_thai_su_dung = fields.Selection(
        [
            ('chua_cap', 'Chưa cấp phát'),
            ('da_cap_phat', 'Đã cấp phát'),
            ('dang_muon', 'Đang được mượn'),
            ('bao_tri', 'Bảo trì'),
            ('hong', 'Hỏng'),
            ('thanh_ly', 'Thanh lý')
        ],
        string="Trạng thái sử dụng",
        default='chua_cap',
        required=True
    )
    
    # === QUẢN LÝ & SỬ DỤNG ===
    nguoi_quan_ly_id = fields.Many2one(
        'nhan_vien',
        string="Người quản lý",
        help="Người được cấp phát và quản lý tài sản này",
        index=True
    )
    
    # Deprecated - giữ để tương thích ngược
    nguoi_su_dung_id = fields.Many2one(
        'nhan_vien',
        string="Người sử dụng (Cũ)",
        help="Field cũ - không sử dụng nữa"
    )
    
    phong_ban_id = fields.Many2one(
        'phong_ban',
        string="Phòng ban",
        help="Phòng ban được cấp tài sản này"
    )
    
    # === MƯỢN TÀI SẢN ===
    nguoi_muon_id = fields.Many2one(
        'nhan_vien',
        string="Người đang mượn",
        readonly=True,
        help="Nhân viên đang mượn tài sản này"
    )
    
    ngay_muon = fields.Datetime("Ngày mượn", readonly=True)
    ngay_du_kien_tra = fields.Datetime("Ngày dự kiến trả", readonly=True)
    
    ghi_chu = fields.Text("Ghi chú")

    ngay_cap = fields.Date("Ngày cấp")
    ngay_thu_hoi = fields.Date("Ngày thu hồi")
    
    # === QUAN HỆ ===
    khau_hao_ids = fields.One2many(
        'khau_hao_tai_san',
        'tai_san_id',
        string="Lịch sử khấu hao"
    )
    bao_tri_ids = fields.One2many(
        'bao_tri_tai_san',
        'tai_san_id',
        string="Lịch sử bảo trì"
    )
    dieu_chuyen_ids = fields.One2many(
        'dieu_chuyen_tai_san',
        'tai_san_id',
        string="Lịch sử điều chuyển"
    )
    phieu_muon_ids = fields.One2many(
        'phieu_muon_tai_san',
        'tai_san_id',
        string="Lịch sử mượn"
    )
    lich_su_ids = fields.One2many(
        'tai_san_lich_su',
        'tai_san_id',
        string="Lịch sử tài sản"
    )
    
    # === COMPUTED METHODS ===
    @api.depends('so_luong', 'gia_mua', 'khau_hao_ids', 'khau_hao_ids.gia_tri_khau_hao')
    def _compute_tong(self):
        """Tính tổng giá mua, khấu hao, giá hiện tại"""
        for r in self:
            r.tong_gia_mua = r.so_luong * r.gia_mua
            # Tính tổng khấu hao
            total_depreciation = sum(r.khau_hao_ids.mapped('gia_tri_khau_hao'))
            r.tong_khau_hao = total_depreciation
            r.tong_gia_hien_tai = r.tong_gia_mua - r.tong_khau_hao
    
    @api.depends('gia_mua', 'khau_hao_ids', 'khau_hao_ids.gia_tri_khau_hao', 'so_luong')
    def _compute_gia_hien_tai(self):
        """Tính giá hiện tại sau khấu hao (mỗi đơn vị)"""
        for r in self:
            total_dep_per_unit = sum(r.khau_hao_ids.mapped('gia_tri_khau_hao')) / (r.so_luong or 1)
            r.gia_hien_tai = r.gia_mua - total_dep_per_unit
    
    @api.depends('thoi_gian_su_dung_du_kien')
    def _compute_ty_le_khau_hao(self):
        """Tính tỷ lệ khấu hao theo thời gian sử dụng"""
        for r in self:
            if r.thoi_gian_su_dung_du_kien > 0:
                r.ty_le_khau_hao = 100.0 / r.thoi_gian_su_dung_du_kien
            else:
                r.ty_le_khau_hao = 0.0
    
    
    def _get_so_luong_muon_qua_phong(self):
        """Helper: Tính số lượng tài sản đang mượn qua phòng họp"""
        self.ensure_one()
        
        try:
            # Kiểm tra module phong_hop có không
            if 'phieu_muon_phong' not in self.env:
                return 0
        
            PhieuMuonPhong = self.env['phieu_muon_phong']
            PhongHopTaiSan = self.env['phong_hop_tai_san']
            
            # Tìm tất cả phòng có tài sản này (cố định)
            phong_co_tai_san = PhongHopTaiSan.search([
                ('tai_san_id', '=', self.id),
                ('la_tai_san_co_dinh', '=', True)
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
                    lambda ts: ts.la_tai_san_co_dinh == True and ts.tai_san_id.id == self.id
                )
                total += sum(ts_trong_phong.mapped('so_luong'))
        
            
            return total
        except Exception as e:
            _logger.warning(
                "Error calculating borrowed quantity via meeting rooms for asset %s: %s",
                self.ten_tai_san if hasattr(self, 'ten_tai_san') else self.id,
                str(e)
            )
            return 0
    
    @api.depends('so_luong')
    def _compute_so_luong_muon(self):
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
            
            # DEBUG LOGGING
            _logger.info(
                "COMPUTE for %s (ID=%s): so_luong=%s, borrowed_direct=%s, borrowed_room=%s, total_borrowed=%s, available=%s",
                r.ten_tai_san, r.id, r.so_luong, so_luong_muon_truc_tiep, 
                so_luong_muon_qua_phong, so_luong_total, r.so_luong - so_luong_total
            )
            
            r.so_luong_dang_muon = so_luong_total
            r.so_luong_kha_dung = r.so_luong - so_luong_total
    
    def action_recalculate_quantity(self):
        """Action button: Tính lại số lượng khả dụng"""
        self._compute_so_luong_muon()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Đã cập nhật số lượng khả dụng!',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def write(self, vals):
        """Kiểm tra quyền khi cập nhật tài sản"""
        # Chỉ quản lý mới được cấp/thu hồi tài sản
        if 'nguoi_quan_ly_id' in vals or 'phong_ban_id' in vals or 'trang_thai_su_dung' in vals:
            if not self.user_has_groups('tai_san.group_asset_manager'):
                raise ValidationError("Chỉ quản lý tài sản mới có quyền cấp/thu hồi tài sản")
        return super().write(vals)
    
    @api.model
    def create(self, vals):
        # Auto-generate mã tài sản nếu chưa có
        if vals.get('ma_tai_san', 'New') == 'New':
            vals['ma_tai_san'] = self.env['ir.sequence'].next_by_code('tai_san') or 'New'
        
        # Validation: chỉ manager mới tạo được
        if not self.user_has_groups('tai_san.group_asset_manager'):
            raise ValidationError("Chỉ quản lý tài sản mới có quyền tạo tài sản mới")
        
        result = super().create(vals)
        result._compute_so_luong_muon()  # Tính số lượng khả dụng ngay
        _logger.info("Created asset %s: %s", result.ma_tai_san, result.ten_tai_san)
        return result
    
    @api.constrains('nguoi_quan_ly_id', 'trang_thai_su_dung')
    def _check_nguoi_quan_ly(self):
        """Kiểm tra tài sản đã cấp phát phải có người quản lý"""
        for record in self:
            if record.trang_thai_su_dung == 'da_cap_phat':
                if not record.nguoi_quan_ly_id:
                    raise ValidationError(
                        "Tài sản đã cấp phát phải có người quản lý"
                    )
    
    @api.constrains('ngay_cap', 'ngay_thu_hoi')
    def _check_ngay(self):
        """Kiểm tra ngày thu hồi phải sau ngày cấp"""
        for record in self:
            if record.ngay_cap and record.ngay_thu_hoi:
                if record.ngay_thu_hoi < record.ngay_cap:
                    raise ValidationError("Ngày thu hồi phải sau ngày cấp")
    
    @api.onchange('trang_thai_su_dung')
    def _onchange_trang_thai_su_dung(self):
        """Tự động cập nhật khi thay đổi trạng thái"""
        if self.trang_thai_su_dung == 'chua_cap':
            self.nguoi_quan_ly_id = False
            self.phong_ban_id = False
            self.nguoi_muon_id = False
            self.ngay_cap = False
        elif self.trang_thai_su_dung == 'thanh_ly':
            self.nguoi_quan_ly_id = False
            self.phong_ban_id = False
            self.nguoi_muon_id = False
            self.ngay_thu_hoi = fields.Date.today()
    
    _sql_constraints = [
        ('ma_tai_san_unique', 'unique(ma_tai_san)', 'Mã tài sản phải là duy nhất')
    ]
