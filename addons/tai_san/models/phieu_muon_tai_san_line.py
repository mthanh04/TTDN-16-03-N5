# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PhieuMuonTaiSanLine(models.Model):
    _name = 'phieu_muon_tai_san_line'
    _description = 'Chi tiết phiếu mượn tài sản'
    
    phieu_muon_id = fields.Many2one(
        'phieu_muon_tai_san',
        string="Phiếu mượn",
        required=True,
        ondelete='cascade'
    )
    
    loai_tai_san_id = fields.Many2one(
        'loai_tai_san',
        string="Loại tài sản",
        required=True,
        help="Chọn loại tài sản để filter danh sách tài sản"
    )
    
    tai_san_id = fields.Many2one(
        'tai_san',
        string="Tài sản",
        required=True,
        domain="[('loai_tai_san_id', '=', loai_tai_san_id), ('trang_thai_su_dung', '=', 'da_cap_phat')]"
    )
    
    # Số lượng mượn
    so_luong = fields.Integer(
        "Số lượng mượn",
        default=1,
        required=True,
        help="Số lượng tài sản muốn mượn"
    )
    
    nguoi_quan_ly_id = fields.Many2one(
        'nhan_vien',
        related='tai_san_id.nguoi_quan_ly_id',
        string="Người quản lý",
        store=True,
        readonly=True
    )
    
    ghi_chu = fields.Text("Ghi chú")
    
    @api.constrains('tai_san_id', 'phieu_muon_id')
    def _check_tai_san_unique(self):
        """Không cho phép mượn trùng tài sản trong cùng 1 phiếu"""
        for record in self:
            duplicate = self.search([
                ('phieu_muon_id', '=', record.phieu_muon_id.id),
                ('tai_san_id', '=', record.tai_san_id.id),
                ('id', '!=', record.id)
            ])
            if duplicate:
                raise ValidationError(
                    f"Tài sản '{record.tai_san_id.ten_tai_san}' đã có trong phiếu mượn này!"
                )
    
    @api.constrains('tai_san_id', 'so_luong')
    def _check_tai_san_availability(self):
        """Kiểm tra tài sản có thể mượn không"""
        for record in self:
            ts = record.tai_san_id
            
            # Kiểm tra số lượng > 0
            if record.so_luong <= 0:
                raise ValidationError("Số lượng mượn phải lớn hơn 0!")
            
            # Kiểm tra trạng thái tài sản
            if ts.trang_thai_su_dung != 'da_cap_phat':
                raise ValidationError(
                    f"Tài sản '{ts.ten_tai_san}' không thể mượn.\n"
                    f"Trạng thái: {dict(ts._fields['trang_thai_su_dung'].selection).get(ts.trang_thai_su_dung)}"
                )
        
            # Kiểm tra đủ số lượng không
            if record.so_luong > ts.so_luong_kha_dung:
                raise ValidationError(
                    f"Tài sản '{ts.ten_tai_san}' không đủ số lượng!\n\n"
                    f"Số lượng muốn mượn: {record.so_luong}\n"
                    f"Tổng số lượng: {ts.so_luong}\n"
                    f"Đang mượn: {ts.so_luong_dang_muon}\n"
                    f"Khả dụng: {ts.so_luong_kha_dung}\n\n"
                    f"Vui lòng giảm xuống {ts.so_luong_kha_dung} hoặc chọn tài sản khác."
                )
