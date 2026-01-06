# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Bảng chấm công nhân viên'
    _rec_name = 'display_name'
    _order = 'ngay_cham desc, nhan_vien_id'

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string='Nhân viên',
        required=True,
        ondelete='cascade'
    )

    ngay_cham = fields.Date(
        string='Ngày chấm công',
        required=True,
        default=fields.Date.context_today
    )

    gio_vao = fields.Datetime(
        string='Giờ vào'
    )

    gio_ra = fields.Datetime(
        string='Giờ ra'
    )

    so_gio_lam = fields.Float(
        string='Số giờ làm việc',
        compute='_compute_so_gio_lam',
        store=True,
        digits=(16, 2)
    )

    trang_thai = fields.Selection(
        [
            ('chua_cham', 'Chưa chấm công'),
            ('da_vao', 'Đã vào'),
            ('da_ra', 'Đã ra')
        ],
        string='Trạng thái',
        compute='_compute_trang_thai',
        store=True
    )

    ghi_chu = fields.Text(string='Ghi chú')

    display_name = fields.Char(
        string='Tên hiển thị',
        compute='_compute_display_name',
        store=True
    )

    # ================= COMPUTE =================

    @api.depends('nhan_vien_id', 'ngay_cham')
    def _compute_display_name(self):
        for r in self:
            if r.nhan_vien_id and r.ngay_cham:
                r.display_name = f"{r.nhan_vien_id.ho_va_ten} - {r.ngay_cham}"
            else:
                r.display_name = "Chấm công"

    @api.depends('gio_vao', 'gio_ra')
    def _compute_so_gio_lam(self):
        for r in self:
            if r.gio_vao and r.gio_ra:
                delta = r.gio_ra - r.gio_vao
                r.so_gio_lam = delta.total_seconds() / 3600
            else:
                r.so_gio_lam = 0

    @api.depends('gio_vao', 'gio_ra')
    def _compute_trang_thai(self):
        for r in self:
            if r.gio_vao and r.gio_ra:
                r.trang_thai = 'da_ra'
            elif r.gio_vao:
                r.trang_thai = 'da_vao'
            else:
                r.trang_thai = 'chua_cham'

    # ================= CONSTRAINT =================

    @api.constrains('gio_vao', 'gio_ra')
    def _check_gio_hop_le(self):
        for r in self:
            if r.gio_vao and r.gio_ra:
                if r.gio_ra < r.gio_vao:
                    raise ValidationError("Giờ ra phải lớn hơn giờ vào")

                if (r.gio_ra - r.gio_vao).total_seconds() / 3600 > 24:
                    raise ValidationError("Số giờ làm việc không được vượt quá 24 giờ")

    @api.constrains('nhan_vien_id', 'ngay_cham')
    def _check_trung_cham_cong(self):
        for r in self:
            if r.nhan_vien_id and r.ngay_cham:
                existed = self.search([
                    ('nhan_vien_id', '=', r.nhan_vien_id.id),
                    ('ngay_cham', '=', r.ngay_cham),
                    ('id', '!=', r.id)
                ])
                if existed:
                    raise ValidationError(
                        f"Nhân viên {r.nhan_vien_id.ho_va_ten} đã được chấm công ngày {r.ngay_cham}"
                    )

    _sql_constraints = [
        (
            'unique_nhan_vien_ngay',
            'unique(nhan_vien_id, ngay_cham)',
            'Mỗi nhân viên chỉ được chấm công một lần trong một ngày!'
        )
    ]
