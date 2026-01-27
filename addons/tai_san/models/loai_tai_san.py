# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LoaiTaiSan(models.Model):
    _name = 'loai_tai_san'
    _description = 'Loại tài sản'
    _rec_name = 'name'
    _order = 'name asc'

    name = fields.Char("Tên loại tài sản", required=True)
    mo_ta = fields.Text("Mô tả")
    
    # Quan hệ với tài sản
    tai_san_ids = fields.One2many(
        'tai_san',
        'loai_tai_san_id',
        string="Danh sách tài sản"
    )
    
    so_luong_tai_san = fields.Integer(
        string="Số lượng tài sản",
        compute="_compute_so_luong_tai_san",
        store=True
    )
    
    @api.depends('tai_san_ids')
    def _compute_so_luong_tai_san(self):
        """Tính số lượng tài sản theo loại"""
        for record in self:
            record.so_luong_tai_san = len(record.tai_san_ids)
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Tên loại tài sản phải là duy nhất')
    ]
