# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class PhongHop(models.Model):
    _name = 'phong_hop'
    _description = 'Phòng họp'
    _rec_name = 'ten_phong'
    _order = 'ma_phong'

    ma_phong = fields.Char("Mã phòng", required=True, index=True, copy=False, default='New')
    ten_phong = fields.Char("Tên phòng", required=True)
    suc_chua = fields.Integer("Sức chứa")
    vi_tri = fields.Char("Vị trí")

    trang_thai = fields.Selection([
        ('san_sang', 'Sẵn sàng'),
        ('dang_su_dung', 'Đang sử dụng'),
        ('bao_tri', 'Bảo trì'),
        ('ngung', 'Ngừng hoạt động')
    ], default='san_sang')

    mo_ta = fields.Text("Mô tả")

    tai_san_ids = fields.One2many('phong_hop_tai_san', 'phong_hop_id', string="Tài sản")

    lich_phong_hop_ids = fields.One2many('lich_phong_hop', 'phong_hop_id', string="Lịch họp")

    phieu_muon_ids = fields.One2many('phieu_muon_phong', 'phong_hop_id', string="Phiếu mượn")
    
    @api.model
    def create(self, vals):
        # Auto-generate mã phòng nếu chưa có
        if vals.get('ma_phong', 'New') == 'New':
            vals['ma_phong'] = self.env['ir.sequence'].next_by_code('phong_hop') or 'New'
        
        result = super().create(vals)
        _logger.info("Created meeting room %s: %s", result.ma_phong, result.ten_phong)
        return result
