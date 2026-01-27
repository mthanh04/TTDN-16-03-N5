# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class DieuChuyenTaiSan(models.Model):
    _name = 'dieu_chuyen_tai_san'
    _description = 'Điều chuyển tài sản'
    _order = 'ngay_dieu_chuyen desc'
    _rec_name = 'name'
    
    name = fields.Char("Số phiếu", default='New', readonly=True, copy=False, index=True)
    
    tai_san_id = fields.Many2one(
        'tai_san',
        string="Tài sản",
        required=True,
        ondelete='restrict'
    )
    
    # Từ
    tu_phong_ban_id = fields.Many2one('phong_ban', string="Từ phòng ban")
    tu_nhan_vien_id = fields.Many2one('nhan_vien', string="Từ nhân viên")
    
    # Đến
    den_phong_ban_id = fields.Many2one('phong_ban', string="Đến phòng ban")
    den_nhan_vien_id = fields.Many2one('nhan_vien', string="Đến nhân viên")
    
    ngay_dieu_chuyen = fields.Date(
        "Ngày điều chuyển",
        required=True,
        default=fields.Date.today,
        index=True
    )
    
    nguoi_phu_trach = fields.Many2one(
        'res.users',
        string="Người phụ trách",
        default=lambda self: self.env.user
    )
    
    ly_do = fields.Text("Lý do điều chuyển", required=True)
    
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('done', 'Hoàn thành'),
        ('rejected', 'Từ chối')
    ], default='draft', string="Trạng thái", tracking=True, required=True)
    
    ly_do_tu_choi = fields.Text("Lý do từ chối")
    
    @api.model
    def create(self, vals):
        """Tự động tạo số phiếu"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('dieu_chuyen_tai_san') or 'New'
        result = super().create(vals)
        _logger.info(f"Created transfer ticket {result.name} for asset {result.tai_san_id.ten_tai_san}")
        return result
    
    @api.constrains('tu_phong_ban_id', 'tu_nhan_vien_id', 'den_phong_ban_id', 'den_nhan_vien_id')
    def _check_nguoi_nhan(self):
        """Validation: phải có ít nhất một nơi đến"""
        for record in self:
            if not record.den_phong_ban_id and not record.den_nhan_vien_id:
                raise ValidationError("Phải chọn ít nhất một nơi đến (phòng ban hoặc nhân viên)")
    
    def action_submit(self):
        """Gửi duyệt"""
        for r in self:
            # Lấy thông tin hiện tại của tài sản để lưu vào "từ"
            if not r.tu_phong_ban_id and not r.tu_nhan_vien_id:
                r.write({
                    'tu_phong_ban_id': r.tai_san_id.phong_ban_id.id,
                    'tu_nhan_vien_id': r.tai_san_id.nguoi_su_dung_id.id
                })
            r.write({'trang_thai': 'cho_duyet'})
            _logger.info(f"Submitted transfer {r.name} for approval")
    
    def action_approve(self):
        """Duyệt và thực hiện điều chuyển"""
        for r in self:
            r.write({'trang_thai': 'approved'})
            
            # Cập nhật tài sản
            r.tai_san_id.write({
                'phong_ban_id': r.den_phong_ban_id.id if r.den_phong_ban_id else False,
                'nguoi_su_dung_id': r.den_nhan_vien_id.id if r.den_nhan_vien_id else False,
                'trang_thai_su_dung': 'dang_dung' if (r.den_phong_ban_id or r.den_nhan_vien_id) else 'chua_cap'
            })
            
            r.write({'trang_thai': 'done'})
            
            _logger.info(
                f"Approved and completed transfer {r.name}: {r.tai_san_id.ten_tai_san} "
                f"from {r.tu_phong_ban_id.name if r.tu_phong_ban_id else r.tu_nhan_vien_id.ho_va_ten if r.tu_nhan_vien_id else 'N/A'} "
                f"to {r.den_phong_ban_id.name if r.den_phong_ban_id else r.den_nhan_vien_id.ho_va_ten if r.den_nhan_vien_id else 'N/A'}"
            )
    
    def action_reject(self):
        """Từ chối điều chuyển"""
        for r in self:
            r.write({'trang_thai': 'rejected'})
            _logger.info(f"Rejected transfer {r.name}")
