# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TaiSanThuHoi(models.Model):
    _name = 'tai_san_thu_hoi'
    _description = 'Thu hồi tài sản'
    _order = 'ngay_thu_hoi desc'

    tai_san_id = fields.Many2one('tai_san', string="Tài sản", required=True)
    ly_do = fields.Text(string="Lý do")
    ngay_thu_hoi = fields.Date(default=fields.Date.today, string="Ngày thu hồi")
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Đã thu hồi')
    ], string="Trạng thái", default='draft')
    
    def action_done(self):
        for rec in self:
            asset = rec.tai_san_id

            # Cập nhật tài sản - Reset về chưa cấp
            asset.write({
                'nguoi_quan_ly_id': False,
                'phong_ban_id': False,
                'nguoi_muon_id': False,
                'ngay_thu_hoi': rec.ngay_thu_hoi,
                'trang_thai_su_dung': 'chua_cap'
            })

            rec.state = 'done'
