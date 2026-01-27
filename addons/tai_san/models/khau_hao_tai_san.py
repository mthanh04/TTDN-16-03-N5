# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class KhauHaoTaiSan(models.Model):
    _name = 'khau_hao_tai_san'
    _description = 'Khấu hao tài sản'
    _order = 'nam desc, thang desc'
    _rec_name = 'name'
    
    name = fields.Char("Tên", compute='_compute_name', store=True)
    
    tai_san_id = fields.Many2one(
        'tai_san',
        string="Tài sản",
        required=True,
        ondelete='cascade',
        index=True
    )
    
    nam = fields.Integer(
        "Năm",
        required=True,
        default=lambda self: fields.Date.today().year,
        index=True
    )
    thang = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12')
    ], string="Tháng", required=True)
    
    gia_tri_khau_hao = fields.Float(
        "Giá trị khấu hao",
        required=True,
        digits=(16, 0),
        help="Giá trị khấu hao trong kỳ"
    )
    
    gia_tri_con_lai = fields.Float(
        "Giá trị còn lại",
        compute='_compute_gia_tri_con_lai',
        store=True,
        digits=(16, 0)
    )
    
    ghi_chu = fields.Text("Ghi chú")
    
    @api.depends('tai_san_id', 'nam', 'thang')
    def _compute_name(self):
        """Tạo tên hiển thị"""
        for record in self:
            if record.tai_san_id and record.nam and record.thang:
                record.name = f"Khấu hao {record.tai_san_id.ten_tai_san} - {record.thang}/{record.nam}"
            else:
                record.name = "Khấu hao tài sản"
    
    @api.depends('tai_san_id', 'tai_san_id.gia_mua', 'tai_san_id.khau_hao_ids', 'gia_tri_khau_hao')
    def _compute_gia_tri_con_lai(self):
        """Tính giá trị còn lại sau khấu hao"""
        for record in self:
            if record.tai_san_id:
                # Tổng khấu hao đến hiện tại (bao gồm bản ghi này)
                total_dep = sum(record.tai_san_id.khau_hao_ids.filtered(
                    lambda r: r.nam < record.nam or (r.nam == record.nam and int(r.thang or '0') <= int(record.thang or '0'))
                ).mapped('gia_tri_khau_hao'))
                
                record.gia_tri_con_lai = record.tai_san_id.tong_gia_mua - total_dep
            else:
                record.gia_tri_con_lai = 0.0
    
    @api.model
    def action_tinh_khau_hao_tu_dong(self):
        """
        Scheduled action chạy hàng tháng để tính khấu hao tự động
        Nên cấu hình chạy vào ngày 1 hàng tháng
        """
        today = fields.Date.today()
        current_year = today.year
        current_month = str(today.month)
        
        # Lấy tất cả tài sản cần tính khấu hao
        tai_sans = self.env['tai_san'].search([
            ('trang_thai_su_dung', 'in', ['dang_dung', 'chua_cap']),
            ('gia_mua', '>', 0),
            ('thoi_gian_su_dung_du_kien', '>', 0)
        ])
        
        created_count = 0
        for ts in tai_sans:
            # Kiểm tra xem đã tính khấu hao cho tháng này chưa
            existing = self.search([
                ('tai_san_id', '=', ts.id),
                ('nam', '=', current_year),
                ('thang', '=', current_month)
            ])
            
            if existing:
                _logger.info(f"Khấu hao for {ts.ten_tai_san} in {current_month}/{current_year} already exists, skipping")
                continue
            
            # Tính giá trị khấu hao
            if ts.phuong_phap_khau_hao == 'duong_thang':
                # Khấu hao đường thẳng
                ty_le = ts.ty_le_khau_hao / 100
                gia_tri_khau_hao_thang = (ts.gia_mua * ty_le) / 12
            else:
                # Số dư giảm dần
                gia_tri_con = ts.gia_hien_tai
                ty_le = ts.ty_le_khau_hao / 100
                gia_tri_khau_hao_thang = (gia_tri_con * ty_le) / 12
            
            # Tạo bản ghi khấu hao
            if gia_tri_khau_hao_thang > 0:
                self.create({
                    'tai_san_id': ts.id,
                    'nam': current_year,
                    'thang': current_month,
                    'gia_tri_khau_hao': gia_tri_khau_hao_thang * ts.so_luong,
                    'ghi_chu': f'Tự động tính khấu hao {ts.phuong_phap_khau_hao}'
                })
                created_count += 1
        
        _logger.info(f"Auto depreciation completed: created {created_count} records")
        return True
    
    _sql_constraints = [
        ('unique_tai_san_period', 
         'unique(tai_san_id, nam, thang)', 
         'Tài sản đã có khấu hao cho kỳ này!')
    ]
