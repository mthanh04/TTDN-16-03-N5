from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError


class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    
    ma_dinh_danh = fields.Char(
        string="Mã nhân viên",
        compute="_compute_ma_dinh_danh",
        store=True,
        readonly=True,
        index=True
    )

    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)

    ho_va_ten = fields.Char(
        string="Họ và tên",
        compute="_compute_ho_va_ten",
        store=True
    )

    ngay_sinh = fields.Date("Ngày sinh")

    tuoi = fields.Integer(
        string="Tuổi",
        compute="_compute_tuoi",
        store=True
    )

    que_quan = fields.Char("Quê quán")
    dia_chi = fields.Text("Địa chỉ")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    so_bhxh = fields.Char("Số BHXH")

    luong = fields.Float("Lương", digits=(16, 0))
    anh = fields.Binary("Ảnh")

   
    lich_su_cong_tac_ids = fields.One2many(
        'lich_su_cong_tac',
        'nhan_vien_id',
        string="Danh sách lịch sử công tác"
    )

    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        'danh_sach_chung_chi_bang_cap',
        'nhan_vien_id',
        string="Danh sách chứng chỉ bằng cấp"
    )

    phong_ban_ids = fields.Many2many(
        'phong_ban',
        'phong_ban_nhan_vien_rel',
        'nhan_vien_id',
        'phong_ban_id',
        string="Danh sách phòng ban"
    )

    so_nguoi_bang_tuoi = fields.Integer(
        string="Số người bằng tuổi",
        compute="_compute_so_nguoi_bang_tuoi",
        store=True
    )

   
    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            record.ho_va_ten = f"{record.ho_ten_dem} {record.ten}".strip()

    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        today = date.today()
        for record in self:
            if record.ngay_sinh:
                record.tuoi = today.year - record.ngay_sinh.year
            else:
                record.tuoi = 0

    @api.depends("ho_ten_dem", "ten", "ngay_sinh")
    def _compute_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten and record.ngay_sinh:
                full_name = f"{record.ho_ten_dem} {record.ten}"
                chu_cai_dau = ''.join(word[0].upper() for word in full_name.split())
                record.ma_dinh_danh = f"{chu_cai_dau}{record.ngay_sinh.strftime('%d%m%Y')}"
            else:
                record.ma_dinh_danh = False

    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if not record.tuoi:
                record.so_nguoi_bang_tuoi = 0
                continue

            domain = [('tuoi', '=', record.tuoi)]
            if record.id:
                domain.append(('id', '!=', record.id))

            record.so_nguoi_bang_tuoi = self.env['nhan_vien'].search_count(domain)


    @api.onchange("ho_ten_dem", "ten", "ngay_sinh")
    def _onchange_ma_dinh_danh(self):
        if self.ho_ten_dem and self.ten and self.ngay_sinh:
            full_name = f"{self.ho_ten_dem} {self.ten}"
            chu_cai_dau = ''.join(word[0].upper() for word in full_name.split())
            self.ma_dinh_danh = f"{chu_cai_dau}{self.ngay_sinh.strftime('%d%m%Y')}"

    
    @api.constrains("tuoi")
    def _check_tuoi(self):
        for record in self:
            if record.tuoi and record.tuoi < 18:
                raise ValidationError("Tuổi nhân viên phải từ 18 trở lên")

    _sql_constraints = [
        (
            'ma_dinh_danh_unique',
            'unique(ma_dinh_danh)',
            'Mã nhân viên đã tồn tại'
        )
    ]
