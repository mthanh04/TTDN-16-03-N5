# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class BaoTriTaiSan(models.Model):
    _name = 'bao_tri_tai_san'
    _description = 'Bảo trì tài sản'
    _order = 'ngay_bao_tri desc'
    _rec_name = 'name'
    
    name = fields.Char("Số phiếu", default='New', readonly=True, copy=False, index=True)
    
    tai_san_id = fields.Many2one(
        'tai_san',
        string="Tài sản",
        required=True,
        ondelete='restrict'
    )
    
    loai_bao_tri = fields.Selection([
        ('bao_tri_dinh_ky', 'Bảo trì định kỳ'),
        ('sua_chua', 'Sửa chữa'),
        ('thay_the_linh_kien', 'Thay thế linh kiện')
    ], string="Loại bảo trì", required=True, default='bao_tri_dinh_ky')
    
    ngay_bao_tri = fields.Date(
        "Ngày bảo trì",
        required=True,
        default=fields.Date.today,
        index=True
    )
    ngay_hoan_thanh = fields.Date("Ngày hoàn thành")
    
    nguoi_thuc_hien = fields.Char("Người thực hiện")
    don_vi_bao_tri = fields.Char("Đơn vị bảo trì", help="Tên công ty/đơn vị thực hiện bảo trì")
    
    chi_phi = fields.Float("Chi phí", digits=(16, 0))
    
    mo_ta_su_co = fields.Text("Mô tả sự cố/nhu cầu bảo trì")
    cach_xu_ly = fields.Text("Cách xử lý/công việc đã thực hiện")
    
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('in_progress', 'Đang sửa'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Hủy')
    ], default='draft', string="Trạng thái", tracking=True, required=True)
    
    @api.model
    def create(self, vals):
        """Tự động tạo số phiếu"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('bao_tri_tai_san') or 'New'
        result = super().create(vals)
        _logger.info(f"Created maintenance ticket {result.name} for asset {result.tai_san_id.ten_tai_san}")
        return result
    
    def action_start(self):
        """Bắt đầu bảo trì"""
        for r in self:
            r.write({
                'trang_thai': 'in_progress',
                'ngay_bao_tri': fields.Date.today()
            })
            # Cập nhật trạng thái tài sản
            r.tai_san_id.write({
                'trang_thai_su_dung': 'bao_tri',
                'tinh_trang': 'sua'
            })
            _logger.info(f"Started maintenance {r.name} for asset {r.tai_san_id.ten_tai_san}")
    
    def action_complete(self):
        """Hoàn thành bảo trì"""
        for r in self:
            r.write({
                'trang_thai': 'done',
                'ngay_hoan_thanh': fields.Date.today()
            })
            # Cập nhật lại trạng thái tài sản
            r.tai_san_id.write({
                'trang_thai_su_dung': 'chua_cap',
                'tinh_trang': 'cu'
            })
            _logger.info(f"Completed maintenance {r.name} for asset {r.tai_san_id.ten_tai_san}, cost: {r.chi_phi}")
    
    def action_cancel(self):
        """Hủy phiếu bảo trì"""
        for r in self:
            r.write({'trang_thai': 'cancelled'})
            # Reset trạng thái tài sản nếu đang bảo trì
            if r.tai_san_id.trang_thai_su_dung == 'bao_tri':
                r.tai_san_id.write({
                    'trang_thai_su_dung': 'chua_cap',
                    'tinh_trang': 'cu'
                })
            _logger.info(f"Cancelled maintenance {r.name}")
