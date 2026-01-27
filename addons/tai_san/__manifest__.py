# -*- coding: utf-8 -*-
{
    'name': "Quản lý Tài sản",
    'summary': "Module quản lý tài sản công ty",
    'description': """
        Module quản lý tài sản:
        - Quản lý loại tài sản và nhà cung cấp
        - Quản lý tài sản với số lượng, giá mua, giá hiện tại
        - Cấp phát tài sản cho nhân viên/phòng ban để quản lý
        - Mượn tài sản tạm thời (workflow đầy đủ)
        - Khấu hao tự động (đường thẳng, số dư giảm dần)
        - Bảo trì và sửa chữa tài sản
        - Điều chuyển tài sản giữa phòng ban/nhân viên
        - Lịch sử mượn/trả tài sản với thời gian
        - Theo dõi trạng thái sử dụng tài sản
        - Báo cáo tài chính và vận hành
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '0.3.1',
    'depends': ['base', 'nhan_su'],
    'data': [
        'data/sequence.xml',
        'data/cron.xml',
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/loai_tai_san.xml',
        'views/nha_cung_cap.xml',
        'views/tai_san.xml',
        'views/tai_san_cap_phat.xml',
        'views/tai_san_thu_hoi.xml',
        'views/tai_san_lich_su.xml',
        'views/phieu_muon_tai_san.xml',
        'views/dashboard.xml',
        'views/menu.xml',
    ],
}
