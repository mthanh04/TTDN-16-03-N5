from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PhongHopTaiSan(models.Model):
    _name = 'phong_hop_tai_san'
    _description = 'Tài sản phòng họp'

    name = fields.Char("Tên tài sản", compute='_compute_name', store=True)
    phong_hop_id = fields.Many2one('phong_hop', string="Phòng họp", required=True, ondelete='cascade')
    
    # Liên kết với model tai_san từ module tai_san
    tai_san_id = fields.Many2one(
        'tai_san',
        string="Tài sản",
        help="Liên kết với tài sản trong module tài sản",
        ondelete='restrict'
    )
    
    loai_tai_san_id = fields.Many2one(
        'loai_tai_san',
        string="Loại tài sản",
        required=True,
        help="Chọn loại tài sản để filter danh sách"
    )

    so_luong = fields.Integer("Số lượng", default=1)
    tinh_trang = fields.Selection([
        ('tot', 'Tốt'),
        ('hong', 'Hỏng'),
        ('sua', 'Đang sửa'),
        ('mat', 'Mất')
    ], string="Tình trạng", default='tot', required=True, tracking=True)

    la_tai_san_co_dinh = fields.Boolean(
        "Tài sản cố định", 
        default=True,
        help="Đánh dấu tài sản này là thiết bị cố định của phòng họp. "
             "Khi mượn phòng, các tài sản cố định sẽ tự động được tính là đang mượn."
    )

    ghi_chu = fields.Text("Ghi chú")
    
    @api.depends('tai_san_id')
    def _compute_name(self):
        """Tự động lấy tên từ tài sản"""
        for record in self:
            if record.tai_san_id:
                record.name = record.tai_san_id.ten_tai_san
            else:
                record.name = "Tài sản mới"
    
    @api.onchange('tai_san_id')
    def _onchange_tai_san_id(self):
        """Tự động cập nhật tên khi chọn tài sản"""
        if self.tai_san_id:
            self.name = self.tai_san_id.ten_tai_san
            # Cập nhật tình trạng từ tài sản
            if self.tai_san_id.tinh_trang == 'hong':
                self.tinh_trang = 'hong'
            elif self.tai_san_id.trang_thai_su_dung == 'bao_tri':
                self.tinh_trang = 'sua'
            else:
                self.tinh_trang = 'tot'
    
    def name_get(self):
        """Override name_get để hiển thị tên tài sản"""
        result = []
        for record in self:
            if record.tai_san_id:
                name = record.tai_san_id.ten_tai_san
            else:
                name = record.name or "Tài sản mới"
            result.append((record.id, name))
        return result
    
    @api.constrains('so_luong', 'tai_san_id')
    def _check_so_luong_tai_san(self):
        """Kiểm tra số lượng tài sản không vượt quá số lượng khả dụng"""
        for record in self:
            if not record.tai_san_id:
                continue
            
            # Tính tổng số lượng tài sản này đã có trong các phòng họp KHÁC (không bao gồm record hiện tại)
            other_phong_tai_san = self.search([
                ('tai_san_id', '=', record.tai_san_id.id),
                ('id', '!=', record.id)  # Loại trừ chính record đang kiểm tra
            ])
            
            # Tổng số lượng hiện có trong các phòng khác
            tong_so_luong_phong_khac = sum(other_phong_tai_san.mapped('so_luong'))
            
            # Số lượng tổng cộng của tài sản
            so_luong_tong = record.tai_san_id.so_luong
            
            # Số lượng sau khi thêm/cập nhật = số lượng ở phòng khác + số lượng muốn thêm
            tong_sau_khi_them = tong_so_luong_phong_khac + record.so_luong
            
            # Kiểm tra: tổng không được vượt quá số lượng tổng cộng
            if tong_sau_khi_them > so_luong_tong:
                so_luong_con_lai = so_luong_tong - tong_so_luong_phong_khac
                raise ValidationError(
                    f"Không đủ số lượng tài sản '{record.tai_san_id.ten_tai_san}'!\n\n"
                    f"📦 Tổng số lượng: {so_luong_tong}\n"
                    f"🏢 Đang có trong các phòng khác: {tong_so_luong_phong_khac}\n"
                    f"➕ Số lượng bạn muốn thêm: {record.so_luong}\n"
                    f"✅ Số lượng khả dụng còn lại: {so_luong_con_lai}\n\n"
                    f"Vui lòng giảm số lượng xuống tối đa {so_luong_con_lai} hoặc chọn tài sản khác."
                )
            
            _logger.info(
                "Validated asset quantity for '%s' in room '%s': %d (available: %d/%d)",
                record.tai_san_id.ten_tai_san,
                record.phong_hop_id.ten_phong,
                record.so_luong,
                so_luong_tong - tong_so_luong_phong_khac,
                so_luong_tong
            )
    
    @api.constrains('tai_san_id', 'la_tai_san_co_dinh')
    def _check_tai_san_availability(self):
        """Kiểm tra tài sản có thể thêm vào phòng họp không"""
        for record in self:
            if not record.tai_san_id:
                continue
            
            # Nếu là tài sản cố định, kiểm tra nghiêm ngặt hơn
            if record.la_tai_san_co_dinh:
                # Kiểm tra tài sản có đang được cấp cho nhân viên/phòng ban không

                

                
                # Kiểm tra tài sản đã thuộc phòng nào khác chưa
                other_phong = self.search([
                    ('tai_san_id', '=', record.tai_san_id.id),
                    ('id', '!=', record.id),
                    ('la_tai_san_co_dinh', '=', True)
                ])
                if other_phong:
                    raise ValidationError(
                        f"Tài sản '{record.tai_san_id.ten_tai_san}' đã là tài sản cố định của phòng "
                        f"'{other_phong[0].phong_hop_id.ten_phong}'. "
                        "Một tài sản chỉ có thể là tài sản cố định của một phòng họp."
                    )
            
            # Kiểm tra trạng thái tài sản
            if record.tai_san_id.trang_thai_su_dung == 'thanh_ly':
                raise ValidationError(
                    f"Tài sản '{record.tai_san_id.ten_tai_san}' đã được thanh lý. "
                    "Không thể thêm vào phòng họp."
                )
            
            _logger.info(
                "Added asset '%s' to meeting room '%s' (Permanent: %s)",
                record.tai_san_id.ten_tai_san,
                record.phong_hop_id.ten_phong,
                record.la_tai_san_co_dinh
            )
    
    @api.constrains('tinh_trang')
    def _check_tinh_trang(self):
        """Validation tình trạng tài sản"""
        for record in self:
            # Tài sản hỏng/mất không được sử dụng trong phòng họp đang hoạt động
            if record.tinh_trang in ['hong', 'mat']:
                # Kiểm tra phòng có đang được sử dụng không
                active_schedules = self.env['lich_phong_hop'].search([
                    ('phong_hop_id', '=', record.phong_hop_id.id),
                    ('trang_thai', 'in', ['cho_duyet', 'approved'])
                ])
                if active_schedules:
                    raise ValidationError(
                        f"Không thể đánh dấu tài sản '{record.name}' là {dict(record._fields['tinh_trang'].selection).get(record.tinh_trang)} "
                        f"khi phòng '{record.phong_hop_id.ten_phong}' đang có lịch sử dụng."
                    )
            
            # Đồng bộ với module tai_san
            if record.tai_san_id:
                if record.tinh_trang == 'hong':
                    record.tai_san_id.write({'tinh_trang': 'hong'})
                    _logger.warning(
                        "Asset '%s' in room '%s' marked as broken",
                        record.name, record.phong_hop_id.ten_phong
                    )
                elif record.tinh_trang == 'sua':
                    record.tai_san_id.write({'trang_thai_su_dung': 'bao_tri'})
                    _logger.info(
                        "Asset '%s' in room '%s' under maintenance",
                        record.name, record.phong_hop_id.ten_phong
                    )
    
    def action_sync_to_tai_san(self):
        """Đồng bộ trạng thái từ phòng họp sang tài sản"""
        for record in self:
            if not record.tai_san_id:
                continue
            
            vals = {}
            if record.tinh_trang == 'hong':
                vals['tinh_trang'] = 'hong'
                vals['trang_thai_su_dung'] = 'hong'
            elif record.tinh_trang == 'sua':
                vals['trang_thai_su_dung'] = 'bao_tri'
            elif record.tinh_trang == 'tot':
                if record.tai_san_id.tinh_trang == 'hong':
                    vals['tinh_trang'] = 'cu'  # Đã sửa xong
                if record.tai_san_id.trang_thai_su_dung == 'bao_tri':
                    vals['trang_thai_su_dung'] = 'chua_cap'
            
            if vals:
                record.tai_san_id.write(vals)
                _logger.info(
                    "Synced asset '%s' status to tai_san module: %s",
                    record.name, vals
                )
        
        return True
    
    def action_remove_tai_san(self):
        """Xóa tài sản khỏi phòng và reset trong module tai_san"""
        for record in self:
            if record.tai_san_id:
                # Reset trạng thái tài sản về chưa cấp
                record.tai_san_id.write({
                    'trang_thai_su_dung': 'chua_cap',
                    'nguoi_su_dung_id': False,
                    'phong_ban_id': False
                })
                _logger.info(
                    "Removed asset '%s' from room '%s' and reset status",
                    record.tai_san_id.ten_tai_san,
                    record.phong_hop_id.ten_phong
                )
            record.unlink()
        
        return True