from odoo import models, fields, api


class LichSuMuonPhong(models.Model):
    _name = 'lich_su_muon_phong'
    _description = 'Lịch sử mượn phòng'
    _order = 'thoi_gian desc'
    _rec_name = 'name'

    name = fields.Char("Tên", compute='_compute_name', store=True)
    
    phieu_id = fields.Many2one('phieu_muon_phong', string="Phiếu mượn", ondelete='cascade')
    phong_hop_id = fields.Many2one('phong_hop', string="Phòng họp", required=True, index=True)
    nguoi_muon_id = fields.Many2one('nhan_vien', string="Người mượn", required=True, index=True)
    lich_phong_hop_id = fields.Many2one('lich_phong_hop', string="Lịch phòng họp", ondelete='set null')

    thoi_gian = fields.Datetime("Thời gian", default=fields.Datetime.now, required=True, index=True)
    
    # Thời gian mượn và trả
    ngay_muon = fields.Datetime("Ngày mượn", help="Thời gian bắt đầu mượn phòng")
    ngay_tra = fields.Datetime("Ngày trả", help="Thời gian trả phòng thực tế")
    ngay_du_kien_tra = fields.Datetime("Ngày dự kiến trả", help="Thời gian dự kiến trả phòng")
    
    hanh_dong = fields.Selection([
        ('muon', 'Mượn'),
        ('tra', 'Trả'),
        ('qua_han', 'Quá hạn')
    ], string="Hành động", required=True)
    
    tai_san_ids = fields.Many2many(
        'phong_hop_tai_san',
        'lich_su_phong_tai_san_rel',
        'lich_su_id',
        'tai_san_id',
        string="Tài sản sử dụng"
    )
    
    ghi_chu = fields.Text("Ghi chú")
    
    @api.depends('phong_hop_id', 'nguoi_muon_id', 'thoi_gian', 'hanh_dong', 'ngay_muon', 'ngay_tra')
    def _compute_name(self):
        """Tạo tên hiển thị cho lịch sử"""
        for record in self:
            if record.phong_hop_id and record.nguoi_muon_id and record.thoi_gian:
                hanh_dong_text = dict(record._fields['hanh_dong'].selection).get(record.hanh_dong, '')
                date_str = fields.Datetime.context_timestamp(
                    record, record.thoi_gian
                ).strftime('%d/%m/%Y %H:%M')
                
                # Thêm thông tin thời gian mượn/trả nếu có
                time_info = ""
                if record.ngay_muon and record.hanh_dong == 'muon':
                    muon_str = fields.Datetime.context_timestamp(
                        record, record.ngay_muon
                    ).strftime('%d/%m %H:%M')
                    if record.ngay_du_kien_tra:
                        tra_str = fields.Datetime.context_timestamp(
                            record, record.ngay_du_kien_tra
                        ).strftime('%d/%m %H:%M')
                        time_info = f" ({muon_str} → {tra_str})"
                    else:
                        time_info = f" (Từ {muon_str})"
                elif record.ngay_tra and record.hanh_dong == 'tra':
                    tra_str = fields.Datetime.context_timestamp(
                        record, record.ngay_tra
                    ).strftime('%d/%m %H:%M')
                    time_info = f" (Trả lúc {tra_str})"
                
                record.name = f"{hanh_dong_text} {record.phong_hop_id.ten_phong} - {record.nguoi_muon_id.ho_va_ten} - {date_str}{time_info}"
            else:
                record.name = "Lịch sử mượn phòng"

