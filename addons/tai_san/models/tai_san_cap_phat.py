# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TaiSanCapPhat(models.Model):
    _name = 'tai_san_cap_phat'
    _description = 'Cấp phát tài sản'
    _order = 'ngay_cap desc'

    tai_san_id = fields.Many2one('tai_san', string="Tài sản", required=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string="Người quản lý", required=True,
                                     help="Nhân viên được cấp phát để quản lý tài sản")
    ngay_cap = fields.Date(default=fields.Date.today, string="Ngày cấp")
    ghi_chu = fields.Text(string="Ghi chú")
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('approved', 'Đã cấp'),
        ('cancel', 'Hủy')
    ], string="Trạng thái", default='draft', tracking=True)

    def action_approve(self):
        """Duyệt cấp phát - gán người quản lý cho tài sản"""
        for rec in self:
            asset = rec.tai_san_id
            
            # Validation: Tài sản đã được cấp phát chưa
            if asset.trang_thai_su_dung == 'da_cap_phat':
                raise ValidationError(
                    f"Tài sản '{asset.ten_tai_san}' đã được cấp phát cho "
                    f"'{asset.nguoi_quan_ly_id.ho_va_ten}'. "
                    "Vui lòng thu hồi trước khi cấp phát lại."
                )
            
            # Validation: Tài sản đang được mượn
            if asset.trang_thai_su_dung == 'dang_muon':
                raise ValidationError(
                    f"Tài sản '{asset.ten_tai_san}' đang được mượn bởi "
                    f"'{asset.nguoi_muon_id.ho_va_ten}'. "
                    "Không thể cấp phát."
                )
            
            # Cập nhật tài sản: gán người quản lý
            asset.write({
                'nguoi_quan_ly_id': rec.nhan_vien_id.id,
                'ngay_cap': rec.ngay_cap,
                'trang_thai_su_dung': 'da_cap_phat'
            })

            rec.state = 'approved'
            
            _logger.info(
                "Asset %s allocated to manager %s",
                asset.ten_tai_san,
                rec.nhan_vien_id.ho_va_ten
            )
    
    def action_cancel(self):
        """Hủy phiếu cấp phát"""
        for rec in self:
            if rec.state == 'approved':
                raise ValidationError(
                    "Không thể hủy phiếu đã cấp phát. "
                    "Vui lòng tạo phiếu thu hồi để thu hồi tài sản."
                )
            rec.state = 'cancel'
