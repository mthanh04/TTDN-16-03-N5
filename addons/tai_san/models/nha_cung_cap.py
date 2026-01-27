# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class NhaCungCap(models.Model):
    _name = 'nha_cung_cap'
    _description = 'Nhà cung cấp'
    _rec_name = 'ten_ncc'
    _order = 'ten_ncc asc'
    
    ma_ncc = fields.Char("Mã nhà cung cấp", required=True, index=True, copy=False)
    ten_ncc = fields.Char("Tên nhà cung cấp", required=True)
    
    dia_chi = fields.Text("Địa chỉ")
    sdt = fields.Char("Số điện thoại")
    email = fields.Char("Email")
    website = fields.Char("Website")
    nguoi_lien_he = fields.Char("Người liên hệ")
    
    ghi_chu = fields.Text("Ghi chú")
    
    # Quan hệ với tài sản
    tai_san_ids = fields.One2many(
        'tai_san',
        'nha_cung_cap_id',
        string="Tài sản cung cấp"
    )
    
    # Computed fields
    so_luong_tai_san = fields.Integer(
        "Số lượng tài sản",
        compute='_compute_so_luong_tai_san',
        store=True
    )
    
    tong_gia_tri_cung_cap = fields.Float(
        "Tổng giá trị cung cấp",
        compute='_compute_tong_gia_tri',
        digits=(16, 0),
        store=True
    )
    
    @api.depends('tai_san_ids')
    def _compute_so_luong_tai_san(self):
        """Tính tổng số lượng tài sản"""
        for record in self:
            record.so_luong_tai_san = sum(record.tai_san_ids.mapped('so_luong'))
    
    @api.depends('tai_san_ids', 'tai_san_ids.tong_gia_mua')
    def _compute_tong_gia_tri(self):
        """Tính tổng giá trị tài sản cung cấp"""
        for record in self:
            record.tong_gia_tri_cung_cap = sum(record.tai_san_ids.mapped('tong_gia_mua'))
    
    _sql_constraints = [
        ('ma_ncc_unique', 'unique(ma_ncc)', 'Mã nhà cung cấp đã tồn tại!')
    ]
