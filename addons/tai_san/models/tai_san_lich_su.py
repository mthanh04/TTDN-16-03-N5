# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TaiSanLichSu(models.Model):
    _name = 'tai_san_lich_su'
    _description = 'Lịch sử tài sản'
    _order = 'ngay desc'

    tai_san_id = fields.Many2one('tai_san', string="Tài sản", required=True, ondelete='cascade')
    phieu_muon_id = fields.Many2one('phieu_muon_tai_san', string="Phiếu mượn", ondelete='set null')
    
    hanh_dong = fields.Selection([
        ('muon', 'Mượn tài sản'),
        ('tra', 'Trả tài sản'),
        ('bao_tri', 'Bảo trì'),
        ('thanh_ly', 'Thanh lý')
    ], string="Hành động", required=True)
    
    # Thông tin người mượn và thời gian
    nguoi_muon_id = fields.Many2one('nhan_vien', string="Người mượn")
    ngay_muon = fields.Datetime("Đã mượn lúc")
    ngay_tra = fields.Datetime("Đã trả lúc")
    ngay_du_kien_tra = fields.Datetime("Dự kiến trả")
    
    ngay = fields.Date(default=fields.Date.today, string="Ngày ghi nhận")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string="Người ghi nhận")
    ghi_chu = fields.Text(string="Ghi chú")
